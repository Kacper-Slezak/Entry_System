import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Enum as SqlEnum, PickleType
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base

class AccessLogStatus(str, enum.Enum):
    GRANTED = "GRANTED"
    DENIED_QR = "DENIED_QR"
    DENIED_FACE = "DENIED_FACE"

class Admin(Base):
    __tablename__ = "admins"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = {'extend_existing': True}

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    is_active = Column(Boolean, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    # PickleType permits saving lists/arrays from DeepFace
    embedding = Column(PickleType, nullable=True)

    #--- Relation to logs ---
    # logs = relationship("AccessLog", back_populates="employee")
    # logs = relationship("app.db.models.AccessLog", back_populates="employee")
    logs = relationship(lambda: AccessLog, back_populates="employee")

class AccessLog(Base):
    __tablename__ = "access_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Entry status
    status = Column(SqlEnum(AccessLogStatus), nullable=False)

    # Reason of rejection
    reason = Column(String, nullable=False)

    # Related key with employees table
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.uuid"), nullable=True)

    # Relation back
    # employee = relationship("Employee", back_populates="logs")
    # employee = relationship("app.db.models.Employee", back_populates="logs")
    employee = relationship(Employee, back_populates="logs")
