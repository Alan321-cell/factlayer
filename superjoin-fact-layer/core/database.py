import sqlite3
import uuid
import chromadb
from chromadb.config import Settings
import json
import os

DB_PATH = "knowledge_layer.sqlite"
CHROMA_PATH = "./chroma_db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create Facts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facts (
            id TEXT PRIMARY KEY,
            topic TEXT,
            subject TEXT,
            predicate TEXT,
            object_value TEXT,
            context TEXT,
            source_document TEXT,
            page_number INTEGER,
            exact_quote TEXT
        )
    ''')
    
    # Create Relationships table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relationships (
            id TEXT PRIMARY KEY,
            fact_1_id TEXT,
            fact_2_id TEXT,
            relationship_type TEXT,
            reasoning TEXT
        )
    ''')
    
    # Create System State table (to track reasoning failures etc.)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id TEXT PRIMARY KEY,
            document_name TEXT,
            log_type TEXT,
            message TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

_CHROMA_CLIENT = None
_CHROMA_COLLECTION = None

def get_chroma_collection():
    global _CHROMA_CLIENT, _CHROMA_COLLECTION
    if _CHROMA_COLLECTION is None:
        try:
            _CHROMA_CLIENT = chromadb.PersistentClient(
                path=CHROMA_PATH,
                settings=Settings(anonymized_telemetry=False)
            )
            _CHROMA_COLLECTION = _CHROMA_CLIENT.get_or_create_collection(name="facts_collection")
        except Exception as e:
            print(f"ChromaDB initialization error: {e}")
            return None
    return _CHROMA_COLLECTION

def insert_fact(fact_dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    fact_id = str(uuid.uuid4())
    src_doc = str(fact_dict.get("source_document", "")).replace("temp_", "")
    
    cursor.execute('''
        INSERT INTO facts (id, topic, subject, predicate, object_value, context, source_document, page_number, exact_quote)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        fact_id,
        fact_dict.get("topic", ""),
        fact_dict.get("subject", ""),
        fact_dict.get("predicate", ""),
        fact_dict.get("object_value", ""),
        fact_dict.get("context", ""),
        src_doc,
        fact_dict.get("page_number", 0),
        fact_dict.get("exact_quote", "")
    ))
    
    conn.commit()
    conn.close()
    
    # Insert into Vector DB (non-blocking / safe)
    try:
        collection = get_chroma_collection()
        if collection is not None:
            semantic_text = f"{fact_dict.get('subject')} {fact_dict.get('predicate')} {fact_dict.get('object_value')}. Context: {fact_dict.get('context')}"
            collection.add(
                documents=[semantic_text],
                metadatas=[{"fact_id": fact_id, "source_document": src_doc}],
                ids=[fact_id]
            )
    except Exception as e:
        print(f"Vector DB addition skipped: {e}")
    
    return fact_id

def insert_relationship(fact_1_id, fact_2_id, relationship_type, reasoning):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Duplicate check: don't re-insert identical fact pairs with same relationship
    cursor.execute('''
        SELECT id FROM relationships 
        WHERE ((fact_1_id = ? AND fact_2_id = ?) OR (fact_1_id = ? AND fact_2_id = ?))
          AND relationship_type = ?
    ''', (fact_1_id, fact_2_id, fact_2_id, fact_1_id, relationship_type))
    if cursor.fetchone():
        conn.close()
        return None

    rel_id = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO relationships (id, fact_1_id, fact_2_id, relationship_type, reasoning)
        VALUES (?, ?, ?, ?, ?)
    ''', (rel_id, fact_1_id, fact_2_id, relationship_type, reasoning))
    
    conn.commit()
    conn.close()
    return rel_id

def insert_system_log(document_name, log_type, message):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    log_id = str(uuid.uuid4())
    doc_clean = str(document_name).replace("temp_", "") if document_name else "System"
    cursor.execute('''
        INSERT INTO system_logs (id, document_name, log_type, message)
        VALUES (?, ?, ?, ?)
    ''', (log_id, doc_clean, log_type, message))
    conn.commit()
    conn.close()
    return log_id

def get_all_documents():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT source_document FROM facts WHERE source_document IS NOT NULL AND source_document != ''")
    facts_docs = [r[0].replace("temp_", "") for r in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT document_name FROM system_logs WHERE document_name IS NOT NULL AND document_name != ''")
    log_docs = [r[0].replace("temp_", "") for r in cursor.fetchall()]
    conn.close()
    return sorted(list(set(facts_docs + log_docs)))

def get_all_facts():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM facts")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_relationships():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Join with facts to get readable output
    cursor.execute('''
        SELECT r.id, r.fact_1_id, r.fact_2_id, r.relationship_type, r.reasoning, 
               f1.subject as f1_sub, f1.predicate as f1_pred, f1.object_value as f1_obj, f1.context as f1_ctx, f1.source_document as f1_doc, f1.exact_quote as f1_quote, f1.page_number as f1_page,
               f2.subject as f2_sub, f2.predicate as f2_pred, f2.object_value as f2_obj, f2.context as f2_ctx, f2.source_document as f2_doc, f2.exact_quote as f2_quote, f2.page_number as f2_page
        FROM relationships r
        JOIN facts f1 ON r.fact_1_id = f1.id
        JOIN facts f2 ON r.fact_2_id = f2.id
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_system_logs():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM system_logs")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_knowledge_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM facts")
    total_facts = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT source_document) FROM facts")
    total_docs = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM relationships")
    total_rels = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM relationships WHERE relationship_type = 'CONTRADICTS'")
    total_contradictions = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM relationships WHERE relationship_type = 'CORROBORATES'")
    total_corroborations = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM relationships WHERE relationship_type = 'RECONCILED'")
    total_reconciled = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT topic) FROM facts")
    total_topics = cursor.fetchone()[0]
    conn.close()
    return {
        "total_facts": total_facts,
        "total_docs": total_docs,
        "total_rels": total_rels,
        "total_contradictions": total_contradictions,
        "total_corroborations": total_corroborations,
        "total_reconciled": total_reconciled,
        "total_topics": total_topics,
    }

def get_schema_evolution():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT source_document, topic, COUNT(*) as fact_count, GROUP_CONCAT(DISTINCT predicate) as sample_predicates
        FROM facts
        GROUP BY source_document, topic
        ORDER BY source_document, fact_count DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
