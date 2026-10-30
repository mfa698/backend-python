import datetime
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, JSON, DateTime, BigInteger, Text, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, relationship

# Modern SQLAlchemy 2.0 declarative base mapper layout class structure
class Base(DeclarativeBase):
    pass


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role_id = Column(Integer, nullable=True)
    keycloak_uuid = Column(String(36), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Contract(Base):
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True, index=True)
    consul_profile_id = Column(Integer, nullable=False)
    date_of_appointment = Column(Date, nullable=False)
    date_of_contract_end = Column(Date, nullable=False)
    cities_of_operation = Column(String, nullable=False)
    is_current_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ContractHistory(Base):
    __tablename__ = "contract_history"
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    previous_end_date = Column(Date, nullable=False)
    extended_to_date = Column(Date, nullable=False)
    authorized_by_user_id = Column(Integer, nullable=False)
    amendment_justification = Column(Text, nullable=False)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)

class WorkLog(Base):
    __tablename__ = "work_logs"
    id = Column(Integer, primary_key=True, index=True)
    consul_user_id = Column(Integer, nullable=False)
    activity_date = Column(Date, default=datetime.date.today, nullable=False)
    activity_notes = Column(Text, nullable=False)
    is_locked = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class QuarterlyReport(Base):
    __tablename__ = "quarterly_reports"
    id = Column(Integer, primary_key=True, index=True)
    consul_user_id = Column(Integer, nullable=False)
    calendar_year = Column(Integer, nullable=False)
    calendar_quarter = Column(Integer, nullable=False)
    structured_payload = Column(Text, nullable=False)
    workflow_status = Column(String(50), default="DRAFT")
    submission_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class PerformanceEvaluation(Base):
    __tablename__ = "performance_evaluations"
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("quarterly_reports.id", ondelete="CASCADE"), nullable=False)
    evaluated_by_hom_id = Column(Integer, nullable=False)
    quantitative_rating = Column(Integer, nullable=False)
    evaluation_notes = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, ForeignKey("performance_evaluations.id", ondelete="CASCADE"), nullable=False)
    recommended_action = Column(String(50), nullable=False)
    detailed_justification = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class DocumentMetadata(Base):
    __tablename__ = "document_metadata"
    id = Column(Integer, primary_key=True, index=True)
    uploaded_by_user_id = Column(Integer, nullable=False)
    file_name = Column(String(255), nullable=False)
    s3_object_key = Column(String(500), unique=True, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    sha256_checksum = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ReportAttachment(Base):
    __tablename__ = "report_attachments"
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("quarterly_reports.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Integer, ForeignKey("document_metadata.id"), nullable=False)
    attachment_label = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(BigInteger, primary_key=True, index=True)
    actor_user_id = Column(Integer, nullable=True)
    action_type = Column(String(100), nullable=False)
    target_resource = Column(String(100), nullable=False)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)

class SystemConfiguration(Base):
    __tablename__ = "system_configurations"
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value_json = Column(JSON, nullable=False)
    updated_by_user_id = Column(Integer, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    recipient_user_id = Column(Integer, nullable=False)
    notification_type = Column(String(50), nullable=False)
    message_content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    dispatched_at = Column(DateTime, default=datetime.datetime.utcnow)

class RenewalCase(Base):
    __tablename__ = "renewal_cases"
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, nullable=False)
    recommendation_id = Column(Integer, nullable=False)
    current_case_status = Column(String(50), default="PENDING_REVIEW")
