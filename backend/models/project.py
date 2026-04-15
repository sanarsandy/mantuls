"""
Project Management ORM Models
- Project: a workspace (like a Trello board)
- ProjectMember: who has access
- Column: Kanban column (e.g. To Do, In Progress, Done)
- Task: a card/ticket inside a column
- TaskComment: comments on a task
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from database import Base
import enum


class MemberRole(str, enum.Enum):
    owner = "owner"
    editor = "editor"
    viewer = "viewer"


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    owner_email = Column(String(255), nullable=False)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    columns = relationship("ProjectColumn", back_populates="project", cascade="all, delete-orphan", order_by="ProjectColumn.position")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")


class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(SAEnum(MemberRole), default=MemberRole.editor)
    joined_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="members")


class ProjectColumn(Base):
    __tablename__ = "project_columns"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    name = Column(String(100), nullable=False)
    position = Column(Integer, default=0)
    color = Column(String(20), default="#6B7280")

    project = relationship("Project", back_populates="columns")
    tasks = relationship("Task", back_populates="column", cascade="all, delete-orphan", order_by="Task.position")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    column_id = Column(String(36), ForeignKey("project_columns.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, default="")
    assignee_email = Column(String(255), nullable=True)
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    due_date = Column(DateTime, nullable=True)
    start_date = Column(DateTime, nullable=True)
    position = Column(Integer, default=0)
    color = Column(String(20), default="#3B82F6")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)

    project = relationship("Project", back_populates="tasks")
    column = relationship("ProjectColumn", back_populates="tasks")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")


class TaskComment(Base):
    __tablename__ = "task_comments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)
    author_email = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="comments")
