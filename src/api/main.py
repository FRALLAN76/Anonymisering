"""REST API for menprovning.

FastAPI-baserat API for dokumentanalys och maskning.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.workflow.orchestrator import create_workflow, WorkflowConfig
from src.core.models import RequesterType


# Pydantic-modeller for API
class TextAnalysisRequest(BaseModel):
    """Request for textanalys."""
    text: str = Field(..., description="Texten att analysera")
    document_id: str = Field(default="unknown", description="Dokument-ID")
    requester_ssn: Optional[str] = Field(None, description="Bestellarens personnummer")
    requester_type: Optional[RequesterType] = Field(None, description="Typ av bestallare")
    requester_party_id: Optional[str] = Field(None, description="Part-ID om bestallaren ar identifierad")
    masking_style: str = Field(default="brackets", description="Maskeringsstil")
    use_llm: bool = Field(default=True, description="Anvand LLM for analys")


class EntityResponse(BaseModel):
    """Entitet i svaret."""
    text: str
    type: str
    start: int
    end: int
    confidence: float


class AssessmentResponse(BaseModel):
    """Bedomning i svaret."""
    category: str
    level: str
    action: str
    confidence: float


class AnalysisResponse(BaseModel):
    """Svar fran analys."""
    document_id: str
    overall_sensitivity: str
    masked_text: str
    entity_count: int
    assessment_count: int
    masked_count: int
    released_count: int
    processing_time_ms: float
    statistics: dict


# Skapa FastAPI-app
app = FastAPI(
    title="Menprovning API",
    description="API for AI-assisterad menprovning enligt OSL",
    version="0.1.0",
)


def get_api_key() -> Optional[str]:
    """Hamta API-nyckel fran miljovariabler."""
    return os.getenv("OPENROUTER_API_KEY")


@app.get("/")
async def root():
    """Rot-endpoint med API-information."""
    return {
        "name": "Menprovning API",
        "version": "0.1.0",
        "endpoints": {
            "/analyze/text": "Analysera text",
            "/analyze/document": "Analysera PDF-dokument",
            "/health": "Halsokontroll",
        }
    }


@app.get("/health")
async def health():
    """Halsokontroll."""
    api_key = get_api_key()
    return {
        "status": "healthy",
        "llm_configured": bool(api_key),
    }


@app.post("/analyze/text", response_model=AnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    """
    Analysera text och returnera maskerad version.

    Tar emot text, kor NER och kanslighetsanalys,
    och returnerar maskerad text enligt OSL.
    """
    try:
        api_key = get_api_key()
        workflow = create_workflow(
            api_key=api_key if request.use_llm else None,
            use_llm=request.use_llm and bool(api_key),
            masking_style=request.masking_style,
        )

        result = workflow.process_text(
            text=request.text,
            document_id=request.document_id,
            requester_ssn=request.requester_ssn,
            requester_type=request.requester_type,
            requester_party_id=request.requester_party_id,
        )

        return AnalysisResponse(
            document_id=result.document_id,
            overall_sensitivity=result.overall_sensitivity.value,
            masked_text=result.masked_text,
            entity_count=len(result.entities),
            assessment_count=len(result.assessments),
            masked_count=result.masking_result.statistics.get("masked_count", 0),
            released_count=result.masking_result.statistics.get("released_count", 0),
            processing_time_ms=result.processing_time_ms,
            statistics=result.statistics,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/document", response_model=AnalysisResponse)
async def analyze_document(
    file: UploadFile = File(...),
    requester_ssn: Optional[str] = Query(None, description="Bestellarens personnummer"),
    requester_type: Optional[RequesterType] = Query(None, description="Typ av bestallare"),
    requester_party_id: Optional[str] = Query(None, description="Part-ID om bestallaren ar identifierad"),
    masking_style: str = Query("brackets", description="Maskeringsstil"),
    use_llm: bool = Query(True, description="Anvand LLM"),
):
    """
    Analysera ett PDF-dokument.

    Ladda upp en PDF-fil for analys och maskning.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Endast PDF-filer stods")

    try:
        # Spara tempor1rt
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            api_key = get_api_key()
            workflow = create_workflow(
                api_key=api_key if use_llm else None,
                use_llm=use_llm and bool(api_key),
                masking_style=masking_style,
            )

            result = workflow.process_document(
                document_path=tmp_path,
                requester_ssn=requester_ssn,
                requester_type=requester_type,
                requester_party_id=requester_party_id,
            )

            return AnalysisResponse(
                document_id=file.filename,
                overall_sensitivity=result.overall_sensitivity.value,
                masked_text=result.masked_text,
                entity_count=len(result.entities),
                assessment_count=len(result.assessments),
                masked_count=result.masking_result.statistics.get("masked_count", 0),
                released_count=result.masking_result.statistics.get("released_count", 0),
                processing_time_ms=result.processing_time_ms,
                statistics=result.statistics,
            )

        finally:
            # Ta bort temporir fil
            Path(tmp_path).unlink(missing_ok=True)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/quick")
async def analyze_quick(request: TextAnalysisRequest):
    """
    Snabb analys utan LLM (endast nyckelord och regex).

    Anvands for forhandsgranskning eller nar LLM inte ar tillganglig.
    """
    try:
        workflow = create_workflow(
            api_key=None,
            use_llm=False,
            masking_style=request.masking_style,
        )

        result = workflow.process_text(
            text=request.text,
            document_id=request.document_id,
            requester_ssn=request.requester_ssn,
            requester_type=request.requester_type,
            requester_party_id=request.requester_party_id,
        )

        return {
            "document_id": result.document_id,
            "overall_sensitivity": result.overall_sensitivity.value,
            "masked_text": result.masked_text,
            "entity_count": len(result.entities),
            "processing_time_ms": result.processing_time_ms,
            "mode": "quick (no LLM)",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# For att kora: uvicorn src.api.main:app --reload
