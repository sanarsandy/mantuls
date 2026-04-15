"""
Project Management Router
Endpoints for projects, columns, tasks, comments, and members.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import asc
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from database import get_db
from models.project import Project, ProjectMember, ProjectColumn, Task, TaskComment, MemberRole
from sso_auth import verify_jwt_token

router = APIRouter(prefix="/api/projects", tags=["projects"])


# ─── Auth helper ────────────────────────────────────────────────────────────────

def get_current_user(authorization: str = "") -> str:
    """Extract email from Bearer JWT. Raises 401 if invalid."""
    from fastapi import Header
    raise HTTPException(status_code=401, detail="Use require_auth dependency")


def require_auth(authorization: Optional[str] = None) -> str:
    """FastAPI dependency that reads Authorization header."""
    from fastapi import Header
    # This wrapper is replaced below using a proper Header dependency
    pass


from fastapi import Header as _Header


def get_user_email(authorization: Optional[str] = _Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1]
    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    email = payload.get("email") or payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Token has no email claim")
    return email


def check_member_access(db: Session, project_id: str, email: str, require_editor: bool = False):
    """Raise 403 if user is not a member (or not an editor when required)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_email == email:
        return project
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.email == email
    ).first()
    if not member:
        if project.is_public and not require_editor:
            return project
        raise HTTPException(status_code=403, detail="Access denied")
    if require_editor and member.role == MemberRole.viewer:
        raise HTTPException(status_code=403, detail="Editor access required")
    return project


# ─── Pydantic schemas ────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    is_public: bool = False


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


class ColumnCreate(BaseModel):
    name: str
    position: int = 0
    color: str = "#6B7280"


class ColumnUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[int] = None
    color: Optional[str] = None


class ColumnReorder(BaseModel):
    column_ids: List[str]  # ordered list


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    column_id: str
    assignee_email: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    position: int = 0
    color: str = "#3B82F6"


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    column_id: Optional[str] = None
    assignee_email: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    position: Optional[int] = None
    color: Optional[str] = None


class TaskMove(BaseModel):
    column_id: str
    position: int


class CommentCreate(BaseModel):
    body: str


class MemberInvite(BaseModel):
    email: str
    role: MemberRole = MemberRole.editor


# ─── Serialisers ─────────────────────────────────────────────────────────────────

def ser_task(t: Task) -> dict:
    return {
        "id": t.id,
        "project_id": t.project_id,
        "column_id": t.column_id,
        "title": t.title,
        "description": t.description,
        "assignee_email": t.assignee_email,
        "priority": t.priority,
        "due_date": t.due_date.isoformat() if t.due_date else None,
        "start_date": t.start_date.isoformat() if t.start_date else None,
        "position": t.position,
        "color": t.color,
        "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        "created_by": t.created_by,
        "comment_count": len(t.comments),
    }


def ser_column(c: ProjectColumn) -> dict:
    return {
        "id": c.id,
        "project_id": c.project_id,
        "name": c.name,
        "position": c.position,
        "color": c.color,
        "tasks": [ser_task(t) for t in sorted(c.tasks, key=lambda x: x.position)],
    }


def ser_project(p: Project, include_columns: bool = False) -> dict:
    data = {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "owner_email": p.owner_email,
        "is_public": p.is_public,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        "member_count": len(p.members) + 1,  # +1 for owner
    }
    if include_columns:
        data["columns"] = [ser_column(c) for c in sorted(p.columns, key=lambda x: x.position)]
        data["members"] = [
            {"email": m.email, "role": m.role.value, "joined_at": m.joined_at.isoformat()}
            for m in p.members
        ]
        data["members"].insert(0, {"email": p.owner_email, "role": "owner", "joined_at": p.created_at.isoformat()})
    return data


# ─── Project endpoints ────────────────────────────────────────────────────────────

@router.get("")
def list_projects(email: str = Depends(get_user_email), db: Session = Depends(get_db)):
    owned = db.query(Project).filter(Project.owner_email == email).all()
    member_project_ids = [
        m.project_id for m in db.query(ProjectMember).filter(ProjectMember.email == email).all()
    ]
    member_projects = db.query(Project).filter(Project.id.in_(member_project_ids)).all()
    seen = {p.id for p in owned}
    all_projects = owned + [p for p in member_projects if p.id not in seen]
    return [ser_project(p) for p in all_projects]


@router.post("", status_code=201)
def create_project(body: ProjectCreate, email: str = Depends(get_user_email), db: Session = Depends(get_db)):
    project = Project(name=body.name, description=body.description, owner_email=email, is_public=body.is_public)
    db.add(project)
    db.flush()

    # Default columns
    defaults = [
        ("To Do", 0, "#6B7280"),
        ("In Progress", 1, "#3B82F6"),
        ("Review", 2, "#F59E0B"),
        ("Done", 3, "#10B981"),
    ]
    for col_name, pos, color in defaults:
        db.add(ProjectColumn(project_id=project.id, name=col_name, position=pos, color=color))

    db.commit()
    db.refresh(project)
    return ser_project(project, include_columns=True)


@router.get("/{project_id}")
def get_project(project_id: str, email: str = Depends(get_user_email), db: Session = Depends(get_db)):
    project = check_member_access(db, project_id, email)
    return ser_project(project, include_columns=True)


@router.patch("/{project_id}")
def update_project(project_id: str, body: ProjectUpdate, email: str = Depends(get_user_email), db: Session = Depends(get_db)):
    project = check_member_access(db, project_id, email, require_editor=True)
    if project.owner_email != email:
        raise HTTPException(status_code=403, detail="Only the owner can edit project settings")
    if body.name is not None:
        project.name = body.name
    if body.description is not None:
        project.description = body.description
    if body.is_public is not None:
        project.is_public = body.is_public
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    return ser_project(project)


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, email: str = Depends(get_user_email), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_email != email:
        raise HTTPException(status_code=403, detail="Only owner can delete")
    db.delete(project)
    db.commit()


# ─── Column endpoints ─────────────────────────────────────────────────────────────

@router.post("/{project_id}/columns", status_code=201)
def create_column(project_id: str, body: ColumnCreate, email: str = Depends(get_user_email), db: Session = Depends(get_db)):
    check_member_access(db, project_id, email, require_editor=True)
    col = ProjectColumn(project_id=project_id, name=body.name, position=body.position, color=body.color)
    db.add(col)
    db.commit()
    db.refresh(col)
    return ser_column(col)


@router.patch("/{project_id}/columns/{column_id}")
def update_column(project_id: str, column_id: str, body: ColumnUpdate, email: str = Depends(get_user_email), db: Session = Depends(get_db)):
    check_member_access(db, project_id, email, require_editor=True)
    col = db.query(ProjectColumn).filter(ProjectColumn.id == column_id, ProjectColumn.project_id == project_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    if body.name is not None:
        col.name = body.name
    if body.position is not None:
        col.position = body.position
    if body.color is not None:
        col.color = body.color
    db.commit()
    db.refresh(col)
    return ser_column(col)


@router.post("/{project_id}/columns/reorder")
def reorder_columns(project_id: str, body: ColumnReorder, email: str = Depends(get_user_email), db: Session = Depends(get_db)):
    check_member_access(db, project_id, email, require_editor=True)
    for idx, col_id in enumerate(body.column_ids):
        db.query(ProjectColumn).filter(
            ProjectColumn.id == col_id, ProjectColumn.project_id == project_id
        ).update({"position": idx})
    db.commit()
    return {"ok": True}


@router.delete("/{project_id}/columns/{column_id}", status_code=204)
def delete_column(project_id: str, column_id: str, email: str = Depends(get_user_email), db: Session = Depends(get_db)):
    check_member_access(db, project_id, email, require_editor=True)
    col = db.query(ProjectColumn).filter(ProjectColumn.id == column_id, ProjectColumn.project_id == project_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    db.delete(col)
    db.commit()


# ─── Task endpoints ───────────────────────────────────────────────────────────────

@router.post("/{project_id}/tasks", status_code=201)
def create_task(project_id: str, body: TaskCreate, email: str = Depends(get_user_email), db: Session = Depends(get_db)):
    check_member_access(db, project_id, email, require_editor=True)
    # Validate column belongs to project
    col = db.query(ProjectColumn).filter(ProjectColumn.id == body.column_id, ProjectColumn.project_id == project_id).first()
    if not col:
        raise HTTPException(status_code=400, detail="Column not in this project")
    task = Task(
        project_id=project_id,
        column_id=body.column_id,
        title=body.title,
        description=body.description,
        assignee_email=body.assignee_email,
        priority=body.priority,
        due_date=body.due_date,
        start_date=body.start_date,
        position=body.position,
        color=body.color,
        created_by=email,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return ser_task(task)


@router.patch("/{project_id}/tasks/{task_id}")
def update_task(project_id: str, task_id: str, body: TaskUpdate, email: str = Depends(get_user_email), db: Session = Depends(get_db)):
    check_member_access(db, project_id, email, require_editor=True)
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, val in body.dict(exclude_none=True).items():
        setattr(task, field, val)
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return ser_task(task)


@router.post("/{project_id}/tasks/{task_id}/move")
def move_task(project_id: str, task_id: str, body: TaskMove, email: str = Depends(get_user_email), db: Session = Depends(get_db)):
    check_member_access(db, project_id, email, require_editor=True)
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    col = db.query(ProjectColumn).filter(ProjectColumn.id == body.column_id, ProjectColumn.project_id == project_id).first()
    if not col:
        raise HTTPException(status_code=400, detail="Column not in this project")
    task.column_id = body.column_id
    task.position = body.position
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return ser_task(task)


@router.delete("/{project_id}/tasks/{task_id}", status_code=204)
def delete_task(project_id: str, task_id: str, email: str = Depends(get_user_email), db: Session = Depends(get_db)):
    check_member_access(db, project_id, email, require_editor=True)
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()


# ─── Comment endpoints ────────────────────────────────────────────────────────────

@router.get("/{project_id}/tasks/{task_id}/comments")
def list_comments(project_id: str, task_id: str, email: str = Depends(get_user_email), db: Session = Depends(get_db)):
    check_member_access(db, project_id, email)
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return [
        {"id": c.id, "author_email": c.author_email, "body": c.body, "created_at": c.created_at.isoformat()}
        for c in task.comments
    ]


@router.post("/{project_id}/tasks/{task_id}/comments", status_code=201)
def add_comment(project_id: str, task_id: str, body: CommentCreate, email: str = Depends(get_user_email), db: Session = Depends(get_db)):
    check_member_access(db, project_id, email, require_editor=True)
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    comment = TaskComment(task_id=task_id, author_email=email, body=body.body)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return {"id": comment.id, "author_email": comment.author_email, "body": comment.body, "created_at": comment.created_at.isoformat()}


@router.delete("/{project_id}/tasks/{task_id}/comments/{comment_id}", status_code=204)
def delete_comment(project_id: str, task_id: str, comment_id: str, email: str = Depends(get_user_email), db: Session = Depends(get_db)):
    comment = db.query(TaskComment).filter(TaskComment.id == comment_id, TaskComment.task_id == task_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.author_email != email:
        raise HTTPException(status_code=403, detail="Not your comment")
    db.delete(comment)
    db.commit()


# ─── Member endpoints ─────────────────────────────────────────────────────────────

@router.post("/{project_id}/members", status_code=201)
def invite_member(project_id: str, body: MemberInvite, email: str = Depends(get_user_email), db: Session = Depends(get_db)):
    project = check_member_access(db, project_id, email, require_editor=True)
    if project.owner_email != email:
        raise HTTPException(status_code=403, detail="Only owner can invite")
    if body.email == project.owner_email:
        raise HTTPException(status_code=400, detail="Owner is already a member")
    existing = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id, ProjectMember.email == body.email
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Already a member")
    member = ProjectMember(project_id=project_id, email=body.email, role=body.role)
    db.add(member)
    db.commit()
    return {"email": member.email, "role": member.role.value}


@router.delete("/{project_id}/members/{member_email}", status_code=204)
def remove_member(project_id: str, member_email: str, email: str = Depends(get_user_email), db: Session = Depends(get_db)):
    project = check_member_access(db, project_id, email, require_editor=True)
    if project.owner_email != email and member_email != email:
        raise HTTPException(status_code=403, detail="Only owner can remove others")
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id, ProjectMember.email == member_email
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
