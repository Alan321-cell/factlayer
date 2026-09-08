from pydantic import BaseModel
from typing import List, Literal, Optional
from openai import OpenAI
import sqlite3
import chromadb
from .database import DB_PATH, get_chroma_collection, insert_relationship, insert_system_log

class IdentifiedRelationship(BaseModel):
    existing_fact_id: str
    relationship_type: Literal["CORROBORATES", "CONTRADICTS", "RECONCILED"]
    reasoning: str

class RelationshipEvaluation(BaseModel):
    relationships: List[IdentifiedRelationship]

def get_fact_by_id(fact_id: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM facts WHERE id = ?", (fact_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def evaluate_new_fact(api_key: Optional[str], new_fact_id: str):
    """Finds similar existing facts and uses LLM (or heuristic reasoning) to identify relationships."""
    new_fact = get_fact_by_id(new_fact_id)
    if not new_fact:
        return
        
    use_openai = bool(api_key and api_key.strip().startswith("sk-"))
    client = OpenAI(api_key=api_key) if use_openai else None
    collection = get_chroma_collection()
    
    # Query Chroma for similar facts
    semantic_text = f"{new_fact.get('subject')} {new_fact.get('predicate')} {new_fact.get('object_value')}. Context: {new_fact.get('context')}"
    
    similar_fact_ids = []
    try:
        results = collection.query(
            query_texts=[semantic_text],
            n_results=6
        )
        similar_fact_ids = [fid for fid in results['ids'][0] if fid != new_fact_id]
    except Exception:
        pass

    # Fallback to SQLite facts if Chroma query returns empty
    if not similar_fact_ids:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM facts WHERE id != ? AND source_document != ? LIMIT 5", (new_fact_id, new_fact.get("source_document", "")))
        rows = cursor.fetchall()
        similar_fact_ids = [r["id"] for r in rows]
        conn.close()
    
    if not similar_fact_ids:
        return
        
    existing_facts = []
    for fid in similar_fact_ids:
        fact_data = get_fact_by_id(fid)
        if fact_data and fact_data.get("source_document") != new_fact.get("source_document"):
            existing_facts.append(fact_data)
            
    if not existing_facts:
        return

    # 1. If OpenAI key is available, run LLM structured evaluation
    if use_openai:
        existing_facts_str = ""
        for f in existing_facts:
            existing_facts_str += f"""
            ID: {f['id']}
            Source: {f['source_document']}
            Subject: {f['subject']}
            Predicate: {f['predicate']}
            Object: {f['object_value']}
            Context: {f['context']}
            Quote: {f['exact_quote']}
            ---
            """
            
        prompt = f"""
        You are a strict data-reconciliation intelligence agent.
        Compare the NEW FACT against the EXISTING FACTS from other documents.
        Identify any relationships:
        - CORROBORATES: They confirm each other.
        - CONTRADICTS: Direct conflict without contextual explanation.
        - RECONCILED: Appear contradictory, but explainable by time, scope, or units.
        
        NEW FACT:
        Source: {new_fact['source_document']}
        Subject: {new_fact['subject']}
        Predicate: {new_fact['predicate']}
        Object: {new_fact['object_value']}
        Context: {new_fact['context']}
        Quote: {new_fact['exact_quote']}
        
        EXISTING FACTS:
        {existing_facts_str}
        """
        
        try:
            response = client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You analyze logical relationships across documents."},
                    {"role": "user", "content": prompt}
                ],
                response_format=RelationshipEvaluation,
            )
            eval_result = response.choices[0].message.parsed
            for rel in eval_result.relationships:
                insert_relationship(new_fact_id, rel.existing_fact_id, rel.relationship_type, rel.reasoning)
            return
        except Exception as e:
            insert_system_log(new_fact.get('source_document', 'Unknown'), "LLM_REASONING_ERROR", str(e))

    # 2. Offline Heuristic Counterfactual Evaluation
    import re
    for f in existing_facts[:3]:
        new_sub = str(new_fact.get("subject", "")).lower()
        ext_sub = str(f.get("subject", "")).lower()
        new_obj = str(new_fact.get("object_value", "")).lower()
        ext_obj = str(f.get("object_value", "")).lower()
        
        # Substantial entity overlap or shared topic
        words_overlap = any(w in ext_sub for w in new_sub.split() if len(w) > 3)
        same_topic = (new_fact.get("topic") == f.get("topic") and new_fact.get("topic") not in ["Document Ingestion", "General"])
        
        if words_overlap or same_topic:
            # Extract years / temporal indicators
            years_new = set(re.findall(r'\b(20\d\d|FY\s*\d\d)\b', f"{new_fact.get('context')} {new_fact.get('exact_quote')}", re.IGNORECASE))
            years_ext = set(re.findall(r'\b(20\d\d|FY\s*\d\d)\b', f"{f.get('context')} {f.get('exact_quote')}", re.IGNORECASE))
            
            has_different_years = bool(years_new and years_ext and not (years_new & years_ext))
            has_scope_difference = any(k in f"{new_fact.get('context')} {new_fact.get('exact_quote')}".lower() for k in ["forecast", "projected", "range", "standalone", "provisional"]) != \
                                   any(k in f"{f.get('context')} {f.get('exact_quote')}".lower() for k in ["forecast", "projected", "range", "standalone", "provisional"])

            # Clean numeric comparison
            num_new = re.findall(r'\d+(?:\.\d+)?', new_obj)
            num_ext = re.findall(r'\d+(?:\.\d+)?', ext_obj)

            if new_obj == ext_obj or (num_new and num_ext and num_new[0] == num_ext[0]):
                insert_relationship(
                    new_fact_id, 
                    f["id"], 
                    "CORROBORATES", 
                    f"Multi-document consensus: Both {new_fact['source_document']} and {f['source_document']} independently corroborate {new_fact.get('subject')} ({new_fact.get('object_value')})."
                )
            elif has_different_years or has_scope_difference:
                v1 = list(years_new)[0] if years_new else 'Period A'
                v2 = list(years_ext)[0] if years_ext else 'Period B'
                insert_relationship(
                    new_fact_id, 
                    f["id"], 
                    "RECONCILED", 
                    f"Apparent contradiction reconciled by context: The variance between {new_fact.get('object_value')} in {new_fact['source_document']} and {f.get('object_value')} in {f['source_document']} is explained by distinct temporal vintages or reporting scopes ({v1} vs {v2})."
                )
            else:
                # Genuine contradiction: same or undefined temporal scope but conflicting metric!
                insert_relationship(
                    new_fact_id, 
                    f["id"], 
                    "CONTRADICTS", 
                    f"Genuine reporting conflict caught: Discrepancy between {new_fact['source_document']} stating {new_fact.get('subject')} as {new_fact.get('object_value')} and {f['source_document']} reporting {f.get('object_value')} for the same operational baseline without qualification."
                )
