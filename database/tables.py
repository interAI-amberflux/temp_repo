from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey, Table, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum

class Role(enum.Enum):
    org_admin = "org_admin"
    process_owner = "process_owner"
    viewer = "viewer"

class MeetingStatus(enum.Enum):
    pending_approval = "pending_approval"
    approved = "approved"
    recorded = "recorded"
    transcribed = "transcribed"

class PGNAdmin(Base):
    __tablename__ = "pgn_admins"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    passwordHash = Column(String, nullable=False)
    mfaEnabled = Column(Boolean, default=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("OrgUser", back_populates="organization")
    meetings = relationship("Meeting", back_populates="organization")

class OrgUser(Base):
    __tablename__ = "org_users"

    id = Column(String, primary_key=True, index=True)
    organizationId = Column(String, ForeignKey("organizations.id"), nullable=False)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False)
    passwordHash = Column(String, nullable=False)
    emailVerified = Column(Boolean, default=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="users")
    createdMeetings = relationship("Meeting", back_populates="createdBy", foreign_keys='Meeting.createdById')
    approvedMeetings = relationship("Meeting", back_populates="approvedBy", foreign_keys='Meeting.approvedById')

class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(String, primary_key=True, index=True)
    role = Column(Enum(Role), unique=True, nullable=False)
    view = Column(Boolean, default=False)
    record = Column(Boolean, default=False)
    upload = Column(Boolean, default=False)
    approve = Column(Boolean, default=False)

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(String, primary_key=True, index=True)
    organizationId = Column(String, ForeignKey("organizations.id"), nullable=False)
    createdById = Column(String, ForeignKey("org_users.id"), nullable=False)
    approvedById = Column(String, ForeignKey("org_users.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(String)
    processType = Column(String)
    tags = Column(JSON)
    status = Column(Enum(MeetingStatus), default=MeetingStatus.pending_approval)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    approvedAt = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization", back_populates="meetings")
    createdBy = relationship("OrgUser", back_populates="createdMeetings", foreign_keys=[createdById])
    approvedBy = relationship("OrgUser", back_populates="approvedMeetings", foreign_keys=[approvedById])
    recordings = relationship("Recording", back_populates="meeting")
    transcriptions = relationship("Transcription", back_populates="meeting")

class Recording(Base):
    __tablename__ = "recordings"

    id = Column(String, primary_key=True, index=True)
    meetingId = Column(String, ForeignKey("meetings.id"), nullable=False)
    s3Url = Column(String, nullable=False)
    recordedAt = Column(DateTime(timezone=True), server_default=func.now())

    meeting = relationship("Meeting", back_populates="recordings")
    transcription = relationship("Transcription", back_populates="recording", uselist=False)

class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(String, primary_key=True, index=True)
    meetingId = Column(String, ForeignKey("meetings.id"), nullable=False)
    recordingId = Column(String, ForeignKey("recordings.id"), unique=True, nullable=False)
    transcriptionText = Column(String, nullable=False)
    transcriptionJson = Column(JSON)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())

    meeting = relationship("Meeting", back_populates="transcriptions")
    recording = relationship("Recording", back_populates="transcription")
    embeddings = relationship("Embedding", back_populates="transcription")

class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(String, primary_key=True, index=True)
    transcriptionId = Column(String, ForeignKey("transcriptions.id"), nullable=False)
    organizationId = Column(String, nullable=False, index=True)
    meetingId = Column(String, nullable=False, index=True)
    qdrantVectorId = Column(String, nullable=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())

    transcription = relationship("Transcription", back_populates="embeddings")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(String, nullable=True)
    role = Column(String, nullable=True)
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    status_code = Column(String, nullable=False)
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
