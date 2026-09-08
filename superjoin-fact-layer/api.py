from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
import shutil
from pathlib import Path
from core.database import (
    init_db,
    get_all_facts,
    get_all_relationships,
    get_system_logs,
    get_knowledge_stats,
    get_schema_evolution,
    get_all_documents,
)
from core.extractor import process_pdf
from core.reasoner import evaluate_new_fact

init_db()

app = FastAPI(
    title="Fact Knowledge Layer API",
    version="1.0.0",
    description="Developer-grade autonomous cross-document fact extraction, grounding, and multi-document logical reconciliation REST API.",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import HTMLResponse, FileResponse

FRONTEND_INDEX = Path(__file__).resolve().parent / "frontend" / "index.html"

@app.get("/", response_class=HTMLResponse, tags=["Web Application"])
def serve_web_ui():
    """Serves the modern Tailwind CSS / Lucide web application."""
    if FRONTEND_INDEX.exists():
        return FileResponse(FRONTEND_INDEX)
    return {
        "service": "Fact Knowledge Layer API",
        "status": "online",
        "interactive_docs": "/docs",
        "stats": get_knowledge_stats()
    }

@app.get("/api/stats", tags=["Analytics & Health"])
def get_stats():
    """Returns real-time knowledge graph metrics: fact counts, relationships, contradictions, and schema evolution."""
    return get_knowledge_stats()

@app.get("/api/facts", tags=["Facts"])
def list_facts(
    document: Optional[str] = Query(None, description="Filter by source document filename"),
    topic: Optional[str] = Query(None, description="Filter by discovered domain taxonomy")
):
    """Retrieve all grounded facts with exact evidence quotes, page numbers, and context."""
    facts = get_all_facts()
    if document:
        doc_clean = document.replace("temp_", "")
        facts = [f for f in facts if f.get("source_document", "").replace("temp_", "") == doc_clean]
    if topic:
        facts = [f for f in facts if f.get("topic") == topic]
    return {"total": len(facts), "facts": facts}

@app.get("/api/relationships", tags=["Reasoning"])
def list_relationships(
    relationship_type: Optional[str] = Query(None, description="Filter by CORROBORATES, CONTRADICTS, or RECONCILED")
):
    """Retrieve cross-document logical relationships and LLM reconciliation reasoning."""
    rels = get_all_relationships()
    if relationship_type:
        rels = [r for r in rels if r.get("relationship_type") == relationship_type.upper()]
    return {"total": len(rels), "relationships": rels}

@app.get("/api/cases", tags=["Evaluation Benchmark"])
def get_four_required_cases(
    document: Optional[str] = Query(None, description="Optional document filter")
):
    """Dedicated endpoint returning the four core assignment cases (Corroboration, Contradiction, Reconciled, Failure Handling)."""
    all_rels = get_all_relationships()
    logs = get_system_logs()
    all_docs = get_all_documents()
    
    filtered_rels = all_rels
    filtered_logs = logs
    if document and document != "ALL":
        doc_clean = document.replace("temp_", "")
        filtered_rels = [
            r for r in all_rels 
            if r.get("f1_doc", "").replace("temp_", "") == doc_clean or r.get("f2_doc", "").replace("temp_", "") == doc_clean
        ]
        filtered_logs = [
            l for l in logs 
            if l.get("document_name", "").replace("temp_", "") == doc_clean
        ]
    
    corroborations = [r for r in filtered_rels if r.get("relationship_type") == "CORROBORATES"]
    contradictions = [r for r in filtered_rels if r.get("relationship_type") == "CONTRADICTS"]
    reconciliations = [r for r in filtered_rels if r.get("relationship_type") == "RECONCILED"]
    
    return {
        "case_1_corroborated": corroborations[0] if corroborations else None,
        "case_2_contradiction": contradictions[0] if contradictions else None,
        "case_3_reconciled": reconciliations[0] if reconciliations else None,
        "corroborations": corroborations,
        "contradictions": contradictions,
        "reconciliations": reconciliations,
        "all_documents": all_docs,
        "case_4_failure_handling": {
            "strategy": "Multi-tier confidence scoring (<0.70 routes to audit log) and VLM multimodal crop fallback",
            "active_logs": filtered_logs
        }
    }

@app.get("/api/schema-evolution", tags=["Taxonomy & Evolution"])
def get_taxonomy_evolution():
    """Inspect dynamic schema adaptation and domain discovery across document vintages."""
    return {"evolution": get_schema_evolution()}

@app.get("/api/logs", tags=["Diagnostic Audit"])
def list_system_logs(
    document: Optional[str] = Query(None, description="Filter by source document filename"),
    log_type: Optional[str] = Query(None, description="Filter by log type")
):
    """Retrieve system diagnostic audit logs: table gating, OCR ambiguities, and guardrail fallbacks."""
    logs = get_system_logs()
    if document and document != "ALL":
        doc_clean = document.replace("temp_", "")
        logs = [l for l in logs if l.get("document_name", "").replace("temp_", "") == doc_clean]
    if log_type:
        logs = [l for l in logs if l.get("log_type") == log_type]
    return {"total": len(logs), "logs": logs}

@app.post("/api/ingest", tags=["Ingestion Pipeline"])
async def ingest_document(
    file: UploadFile = File(...),
    openai_api_key: Optional[str] = Form(None)
):
    """Upload any arbitrary PDF document for automated extraction, grounding, and incremental reasoning."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF documents are supported.")
        
    clean_filename = file.filename.replace("temp_", "")
    temp_dir = Path("./uploaded_docs")
    temp_dir.mkdir(exist_ok=True)
    save_path = temp_dir / clean_filename
    
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        new_fact_ids = process_pdf(openai_api_key, str(save_path))
        
        # Incremental counterfactual evaluation against existing knowledge (top representative claims)
        for fid in new_fact_ids[:6]:
            evaluate_new_fact(openai_api_key, fid)
            
        return {
            "status": "success",
            "message": f"Successfully extracted {len(new_fact_ids)} grounded claims from {clean_filename} and updated knowledge layer.",
            "filename": clean_filename,
            "extracted_facts_count": len(new_fact_ids),
            "fact_ids": new_fact_ids
        }
    finally:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
