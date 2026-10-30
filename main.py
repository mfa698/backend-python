import datetime
import json
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from sqlalchemy import select

# Import all core entities securely from our schema model library
from model import (
    Base, User, Contract, ContractHistory, WorkLog, QuarterlyReport, AuditLog,
    PerformanceEvaluation, Recommendation, DocumentMetadata, ReportAttachment,
    SystemConfiguration, Notification, RenewalCase
)

DATABASE_URL = "sqlite+aiosqlite:///./ehcms_production.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

app = FastAPI(
    title="e-HCMS Comprehensive Engine",
    description="Unified Group B Backend executing 100% of the relational data schema.",
    version="1.1.0"
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

@app.on_event("startup")
async def verify_and_initialize_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# --- Pydantic Validation Enforcers for the Remaining Entities ---
class EvaluationSubmit(BaseModel):
    report_id: int
    evaluated_by_hom_id: int
    quantitative_rating: int = Field(..., ge=1, le=10)
    evaluation_notes: str
    recommended_action: str # RENEW_CONTRACT or TERMINATE_APPOINTMENT
    detailed_justification: str

class FileMetadataRegister(BaseModel):
    uploaded_by_user_id: int
    report_id: int
    file_name: str
    s3_object_key: str
    mime_type: str
    file_size_bytes: int
    sha256_checksum: str

class ConfigurationUpdate(BaseModel):
    config_key: str
    config_value_json: Dict[str, Any]
    updated_by_user_id: int

# =====================================================================
# ACTIVATING EXTENDED ENTITY OPERATIONS CHANNELS
# =====================================================================

@app.post("/api/v1/evaluations/submit", status_code=status.HTTP_201_CREATED)
async def submit_ambassador_evaluation(payload: EvaluationSubmit, db: AsyncSession = Depends(get_db)):
    """
    Activates Entities 14 & 15 (PerformanceEvaluation & Recommendation).
    Allows supervising Ambassadors to attach evaluations and recommendations directly to quarterly reports.
    """
    # 1. Instantiate the evaluation block entity metrics
    new_eval = PerformanceEvaluation(
        report_id=payload.report_id,
        evaluated_by_hom_id=payload.evaluated_by_hom_id,
        quantitative_rating=payload.quantitative_rating,
        evaluation_notes=payload.evaluation_notes
    )
    db.add(new_eval)
    await db.flush() # Secure child primary key allocation sequence

    # 2. Instantiate and bind the tracking recommendation entity
    new_recom = Recommendation(
        evaluation_id=new_eval.id,
        recommended_action=payload.recommended_action,
        detailed_justification=payload.detailed_justification
    )
    db.add(new_recom)

    # 3. Commit operation to System Audit Trail logs
    audit = AuditLog(
        actor_user_id=payload.evaluated_by_hom_id,
        action_type="AMBASSADOR_EVALUATION_SUBMITTED",
        target_resource=f"reports:id_{payload.report_id}"
    )
    db.add(audit)
    return {"status": "SUCCESS", "message": "Performance evaluation and mission recommendation recorded."}


@app.post("/api/v1/documents/register", status_code=status.HTTP_201_CREATED)
async def register_uploaded_document_metadata(payload: FileMetadataRegister, db: AsyncSession = Depends(get_db)):
    """
    Activates Entities 12 & 13 (DocumentMetadata & ReportAttachment).
    Registers document metrics and links uploaded files directly to quarterly reports.
    """
    new_doc = DocumentMetadata(
        uploaded_by_user_id=payload.uploaded_by_user_id,
        file_name=payload.file_name,
        s3_object_key=payload.s3_object_key,
        mime_type=payload.mime_type,
        file_size_bytes=payload.file_size_bytes,
        sha256_checksum=payload.sha256_checksum
    )
    db.add(new_doc)
    await db.flush()

    new_attach = ReportAttachment(
        report_id=payload.report_id,
        document_id=new_doc.id,
        attachment_label="Quarterly Proof Document Metadata Asset"
    )
    db.add(new_attach)
    return {"status": "SUCCESS", "document_id": new_doc.id, "message": "File tracking metadata linked to target report."}


@app.post("/api/v1/system/configure", status_code=status.HTTP_200_OK)
async def update_global_system_configurations(payload: ConfigurationUpdate, db: AsyncSession = Depends(get_db)):
    """
    Activates Entity 18 (SystemConfiguration).
    Allows MFDA HQ to dynamically update system settings and alert parameters.
    """
    query = select(SystemConfiguration).where(SystemConfiguration.config_key == payload.config_key)
    res = await db.execute(query)
    config = res.scalar_one_or_none()

    if config:
        config.config_value_json = payload.config_value_json
        config.updated_by_user_id = payload.updated_by_user_id
    else:
        config = SystemConfiguration(
            config_key=payload.config_key,
            config_value_json=payload.config_value_json,
            updated_by_user_id=payload.updated_by_user_id
        )
        db.add(config)
        
    return {"status": "SUCCESS", "message": "Global execution parameters adjusted dynamically."}

# --- Retain Baseline Legacy Routes for UI Operations Continuity ---
class WorkLogCreate(BaseModel):
    consul_user_id: int
    activity_notes: str

@app.post("/api/v1/worklogs", status_code=status.HTTP_201_CREATED)
async def submit_immutable_work_log(payload: WorkLogCreate, db: AsyncSession = Depends(get_db)):
    new_log = WorkLog(consul_user_id=payload.consul_user_id, activity_notes=payload.activity_notes, is_locked=True)
    db.add(new_log)
    db.add(AuditLog(actor_user_id=payload.consul_user_id, action_type="WORKLOG_LOCKED", target_resource="work_logs"))
    return {"status": "SUCCESS"}

@app.get("/api/v1/contracts/expiration-alerts")
async def run_expiry_alerts_engine(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contract))
    rows = result.scalars().all()
    active_alerts = []
    for contract in rows:
        days_remaining = (contract.date_of_contract_end - datetime.date.today()).days
        active_alerts.append({
            "contract_id": contract.id,
            "expiration_date": contract.date_of_contract_end.isoformat(),
            "days_left": days_remaining,
            "status_flag": "CRITICAL_30_DAYS" if days_remaining <= 30 else "NORMAL",
            "alert_message": "Automated warning computed."
        })
    return active_alerts
