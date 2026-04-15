"""
Whiteboard Router — REST + WebSocket for collaborative Excalidraw sessions.

Auth strategy:
  - REST  : Authorization: Bearer <jwt>  (sent by frontend from ocr_token cookie)
  - WS    : ?token=<jwt>                 (query param, browser WS API can't set headers)
"""
import json
import secrets
import logging
from datetime import datetime, timezone
from typing import Dict, Set, Optional, List

from fastapi import (
    APIRouter, Depends, Header, HTTPException, WebSocket,
    WebSocketDisconnect, Query
)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.whiteboard import WhiteboardRoom, WhiteboardSnapshot, WhiteboardMember
from sso_auth import verify_jwt_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/whiteboard", tags=["whiteboard"])

# ── Cursor colour palette ────────────────────────────────────────────────────
_COLORS = [
    "#e03131", "#2f9e44", "#1971c2", "#f08c00",
    "#9c36b5", "#0c8599", "#e8590c", "#364fc7",
]

# Max snapshots kept per room (oldest pruned automatically)
MAX_SNAPSHOTS = 50


# ═══════════════════════════════════════════════════════════════════════════════
#  In-memory Collaboration State
# ═══════════════════════════════════════════════════════════════════════════════

class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, Set[WebSocket]] = {}
        self.user_info: Dict[WebSocket, dict] = {}
        self.room_color_idx: Dict[str, int] = {}
        # Live canvas state (elements + appState) per room
        self.room_states: Dict[str, dict] = {}

    def _next_color(self, room_id: str) -> str:
        idx = self.room_color_idx.get(room_id, 0)
        self.room_color_idx[room_id] = idx + 1
        return _COLORS[idx % len(_COLORS)]

    async def connect(self, ws: WebSocket, room_id: str, user: dict):
        await ws.accept()
        self.rooms.setdefault(room_id, set()).add(ws)
        self.user_info[ws] = {
            "email": user.get("email", ""),
            "name": user.get("name", user.get("email", "Unknown")),
            "color": self._next_color(room_id),
            "room_id": room_id,
        }

    async def disconnect(self, ws: WebSocket) -> tuple:
        info = self.user_info.pop(ws, {})
        room_id = info.get("room_id")
        if room_id and room_id in self.rooms:
            self.rooms[room_id].discard(ws)
            if not self.rooms[room_id]:
                del self.rooms[room_id]
        return info, room_id

    async def broadcast(self, room_id: str, message: dict, exclude: WebSocket = None):
        dead: Set[WebSocket] = set()
        for ws in list(self.rooms.get(room_id, [])):
            if ws is exclude:
                continue
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.rooms.get(room_id, set()).discard(ws)

    def get_online_users(self, room_id: str) -> List[dict]:
        return [
            {
                "email": self.user_info[ws]["email"],
                "name": self.user_info[ws]["name"],
                "color": self.user_info[ws]["color"],
            }
            for ws in self.rooms.get(room_id, [])
            if ws in self.user_info
        ]

    def set_room_state(self, room_id: str, elements: list, app_state: dict):
        self.room_states[room_id] = {"elements": elements, "appState": app_state}

    def get_room_state(self, room_id: str) -> dict:
        return self.room_states.get(room_id, {"elements": [], "appState": {}})


manager = ConnectionManager()


# ═══════════════════════════════════════════════════════════════════════════════
#  Auth helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _user_from_header(authorization: Optional[str]) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization[7:]
    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


def _user_from_token(token: str) -> Optional[dict]:
    if not token:
        return None
    return verify_jwt_token(token)


def _check_access(room: WhiteboardRoom, email: str, need_editor: bool = False) -> bool:
    if room.owner_email == email:
        return True
    for m in room.members:
        if m.email == email:
            return not (need_editor and m.role == "viewer")
    return room.is_public and not need_editor


# ═══════════════════════════════════════════════════════════════════════════════
#  Pydantic schemas
# ═══════════════════════════════════════════════════════════════════════════════

class RoomCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    is_public: bool = False


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


class MemberAdd(BaseModel):
    email: str
    role: str = "editor"   # "editor" | "viewer"


class SnapshotSave(BaseModel):
    elements: list
    app_state: dict = {}
    thumbnail: Optional[str] = None   # base64 PNG from Excalidraw exportToBlob
    label: Optional[str] = "Manual save"


# ═══════════════════════════════════════════════════════════════════════════════
#  REST — Room CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/rooms", status_code=201)
def create_room(
    body: RoomCreate,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    user = _user_from_header(authorization)
    room = WhiteboardRoom(
        id=secrets.token_hex(16),
        name=body.name,
        description=body.description or "",
        owner_email=user["email"],
        is_public=body.is_public,
        share_token=secrets.token_urlsafe(32),
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    logger.info(f"Room created: {room.id} by {user['email']}")
    return _room_dict(room, user["email"])


@router.get("/rooms")
def list_rooms(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    user = _user_from_header(authorization)
    email = user["email"]

    owned = db.query(WhiteboardRoom).filter(WhiteboardRoom.owner_email == email).all()
    member_room_ids = [
        m.room_id for m in
        db.query(WhiteboardMember).filter(WhiteboardMember.email == email).all()
    ]
    shared = db.query(WhiteboardRoom).filter(
        WhiteboardRoom.id.in_(member_room_ids),
        WhiteboardRoom.owner_email != email
    ).all()

    return {
        "owned": [_room_dict(r, email) for r in owned],
        "shared": [_room_dict(r, email) for r in shared],
    }


@router.get("/rooms/{room_id}")
def get_room(
    room_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    user = _user_from_header(authorization)
    room = _get_room_or_404(room_id, db)
    if not _check_access(room, user["email"]):
        raise HTTPException(status_code=403, detail="Access denied")

    # Return live state if someone is in the room, otherwise DB state
    live = manager.get_room_state(room_id)
    elements = live["elements"] if live["elements"] else json.loads(room.current_data or "[]")
    app_state = live["appState"] if live["appState"] else json.loads(room.current_app_state or "{}")

    result = _room_dict(room, user["email"])
    result["elements"] = elements
    result["app_state"] = app_state
    result["online_users"] = manager.get_online_users(room_id)
    return result


@router.patch("/rooms/{room_id}")
def update_room(
    room_id: str,
    body: RoomUpdate,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    user = _user_from_header(authorization)
    room = _get_room_or_404(room_id, db)
    if room.owner_email != user["email"]:
        raise HTTPException(status_code=403, detail="Only the owner can edit room settings")

    if body.name is not None:
        room.name = body.name
    if body.description is not None:
        room.description = body.description
    if body.is_public is not None:
        room.is_public = body.is_public
    room.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(room)
    return _room_dict(room, user["email"])


@router.delete("/rooms/{room_id}", status_code=204)
def delete_room(
    room_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    user = _user_from_header(authorization)
    room = _get_room_or_404(room_id, db)
    if room.owner_email != user["email"]:
        raise HTTPException(status_code=403, detail="Only the owner can delete this room")
    db.delete(room)
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
#  REST — Members
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/rooms/{room_id}/members", status_code=201)
def add_member(
    room_id: str,
    body: MemberAdd,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    user = _user_from_header(authorization)
    room = _get_room_or_404(room_id, db)
    if room.owner_email != user["email"]:
        raise HTTPException(status_code=403, detail="Only the owner can manage members")
    if body.role not in ("editor", "viewer"):
        raise HTTPException(status_code=400, detail="role must be 'editor' or 'viewer'")

    existing = db.query(WhiteboardMember).filter_by(room_id=room_id, email=body.email).first()
    if existing:
        existing.role = body.role
    else:
        db.add(WhiteboardMember(room_id=room_id, email=body.email, role=body.role))
    db.commit()
    return {"ok": True, "email": body.email, "role": body.role}


@router.delete("/rooms/{room_id}/members/{email}", status_code=204)
def remove_member(
    room_id: str,
    email: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    user = _user_from_header(authorization)
    room = _get_room_or_404(room_id, db)
    if room.owner_email != user["email"]:
        raise HTTPException(status_code=403, detail="Only the owner can manage members")
    db.query(WhiteboardMember).filter_by(room_id=room_id, email=email).delete()
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
#  REST — Snapshots / History
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/rooms/{room_id}/history")
def list_history(
    room_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    user = _user_from_header(authorization)
    room = _get_room_or_404(room_id, db)
    if not _check_access(room, user["email"]):
        raise HTTPException(status_code=403, detail="Access denied")

    snaps = (
        db.query(WhiteboardSnapshot)
        .filter_by(room_id=room_id)
        .order_by(WhiteboardSnapshot.created_at.desc())
        .all()
    )
    return [_snap_dict(s) for s in snaps]


@router.post("/rooms/{room_id}/save", status_code=201)
def save_snapshot(
    room_id: str,
    body: SnapshotSave,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    user = _user_from_header(authorization)
    room = _get_room_or_404(room_id, db)
    if not _check_access(room, user["email"], need_editor=True):
        raise HTTPException(status_code=403, detail="Editor access required")

    app_state_clean = {
        k: v for k, v in (body.app_state or {}).items()
        if k not in ("collaborators",)
    }
    snap = WhiteboardSnapshot(
        room_id=room_id,
        data=json.dumps(body.elements),
        app_state=json.dumps(app_state_clean),
        thumbnail=body.thumbnail,
        saved_by=user["email"],
        label=body.label or "Manual save",
    )
    db.add(snap)

    # Also persist as current room state
    room.current_data = json.dumps(body.elements)
    room.current_app_state = json.dumps(app_state_clean)
    room.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(snap)

    # Prune old auto-saves to stay under MAX_SNAPSHOTS
    _prune_snapshots(room_id, db)

    return _snap_dict(snap)


@router.post("/rooms/{room_id}/restore/{snapshot_id}")
async def restore_snapshot(
    room_id: str,
    snapshot_id: int,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    user = _user_from_header(authorization)
    room = _get_room_or_404(room_id, db)
    if not _check_access(room, user["email"], need_editor=True):
        raise HTTPException(status_code=403, detail="Editor access required")

    snap = db.query(WhiteboardSnapshot).filter_by(id=snapshot_id, room_id=room_id).first()
    if not snap:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    elements = json.loads(snap.data)
    app_state = json.loads(snap.app_state or "{}")

    # Update DB state
    room.current_data = snap.data
    room.current_app_state = snap.app_state or "{}"
    room.updated_at = datetime.utcnow()
    db.commit()

    # Update in-memory state & broadcast to all connected users
    manager.set_room_state(room_id, elements, app_state)
    await manager.broadcast(room_id, {
        "type": "restore",
        "elements": elements,
        "appState": app_state,
        "by": user["email"],
        "label": snap.label,
    })

    return {"ok": True, "snapshot_id": snapshot_id}


@router.delete("/rooms/{room_id}/history/{snapshot_id}", status_code=204)
def delete_snapshot(
    room_id: str,
    snapshot_id: int,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    user = _user_from_header(authorization)
    room = _get_room_or_404(room_id, db)
    if room.owner_email != user["email"]:
        raise HTTPException(status_code=403, detail="Only the owner can delete snapshots")
    db.query(WhiteboardSnapshot).filter_by(id=snapshot_id, room_id=room_id).delete()
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
#  REST — Share token
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/rooms/{room_id}/regenerate-token")
def regenerate_share_token(
    room_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    user = _user_from_header(authorization)
    room = _get_room_or_404(room_id, db)
    if room.owner_email != user["email"]:
        raise HTTPException(status_code=403, detail="Only the owner can manage share links")
    room.share_token = secrets.token_urlsafe(32)
    db.commit()
    return {"share_token": room.share_token}


# ═══════════════════════════════════════════════════════════════════════════════
#  WebSocket — Real-time collaboration
# ═══════════════════════════════════════════════════════════════════════════════

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    # 1. Verify JWT
    user = _user_from_token(token)
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    # 2. Verify room access
    room = db.query(WhiteboardRoom).filter_by(id=room_id).first()
    if not room or not _check_access(room, user["email"]):
        await websocket.close(code=4003, reason="Room not found or access denied")
        return

    is_editor = _check_access(room, user["email"], need_editor=True)

    # 3. Connect
    await manager.connect(websocket, room_id, user)
    logger.info(f"WS connect: {user['email']} → room {room_id}")

    # 4. Send initial sync to this user
    state = manager.get_room_state(room_id)
    elements = state["elements"] if state["elements"] else json.loads(room.current_data or "[]")
    app_state = state["appState"] if state["appState"] else json.loads(room.current_app_state or "{}")

    await websocket.send_text(json.dumps({
        "type": "sync",
        "elements": elements,
        "appState": app_state,
        "online_users": manager.get_online_users(room_id),
        "is_editor": is_editor,
    }))

    # 5. Announce join to others
    await manager.broadcast(room_id, {
        "type": "presence",
        "action": "join",
        "user": {
            "email": user["email"],
            "name": user.get("name", user["email"]),
            "color": manager.user_info[websocket]["color"],
        },
        "online_users": manager.get_online_users(room_id),
    }, exclude=websocket)

    # 6. Message loop
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            if msg_type == "update" and is_editor:
                elements = msg.get("elements", [])
                app_state = msg.get("appState", {})

                # Strip runtime-only keys that cannot be JSON-serialised
                # (collaborators is a Map in JS → becomes {} after JSON round-trip,
                #  which crashes Excalidraw's UserList component)
                app_state_clean = {
                    k: v for k, v in app_state.items()
                    if k not in ("collaborators",)
                }

                # Update live in-memory state
                manager.set_room_state(room_id, elements, app_state_clean)

                # Persist to DB
                room.current_data = json.dumps(elements)
                room.current_app_state = json.dumps(app_state_clean)
                room.updated_at = datetime.utcnow()
                db.commit()

                # Broadcast to others
                await manager.broadcast(room_id, {
                    "type": "update",
                    "elements": elements,
                    "appState": app_state,
                    "from": user["email"],
                }, exclude=websocket)

            elif msg_type == "cursor":
                await manager.broadcast(room_id, {
                    "type": "cursor",
                    "x": msg.get("x", 0),
                    "y": msg.get("y", 0),
                    "email": user["email"],
                    "color": manager.user_info.get(websocket, {}).get("color", "#000"),
                }, exclude=websocket)

            elif msg_type == "autosave" and is_editor:
                # Use the in-memory state (always up-to-date from prior "update"
                # messages) instead of client-sent data, so we never snapshot
                # a stale or empty canvas.
                live = manager.get_room_state(room_id)
                elements = live.get("elements", [])
                app_state_clean = {
                    k: v for k, v in live.get("appState", {}).items()
                    if k not in ("collaborators",)
                }

                # Skip if canvas is still empty (nothing to save)
                if not elements:
                    continue

                snap = WhiteboardSnapshot(
                    room_id=room_id,
                    data=json.dumps(elements),
                    app_state=json.dumps(app_state_clean),
                    saved_by=user["email"],
                    label="Auto-save",
                )
                db.add(snap)
                room.current_data = json.dumps(elements)
                room.current_app_state = json.dumps(app_state_clean)
                room.updated_at = datetime.utcnow()
                db.commit()
                _prune_snapshots(room_id, db)
                logger.info(f"Auto-saved room {room_id} ({len(elements)} elements)")

            elif msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket)
        logger.info(f"WS disconnect: {user['email']} ← room {room_id}")
        await manager.broadcast(room_id, {
            "type": "presence",
            "action": "leave",
            "user": {"email": user["email"]},
            "online_users": manager.get_online_users(room_id),
        })
        # Note: db session is closed automatically by FastAPI's get_db dependency


# ═══════════════════════════════════════════════════════════════════════════════
#  Internal helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _get_room_or_404(room_id: str, db: Session) -> WhiteboardRoom:
    room = db.query(WhiteboardRoom).filter_by(id=room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


def _room_dict(room: WhiteboardRoom, viewer_email: str) -> dict:
    return {
        "id": room.id,
        "name": room.name,
        "description": room.description,
        "owner_email": room.owner_email,
        "is_owner": room.owner_email == viewer_email,
        "is_public": room.is_public,
        "share_token": room.share_token,
        "members": [
            {"email": m.email, "role": m.role}
            for m in room.members
        ],
        "created_at": room.created_at.isoformat() if room.created_at else None,
        "updated_at": room.updated_at.isoformat() if room.updated_at else None,
    }


def _snap_dict(snap: WhiteboardSnapshot) -> dict:
    return {
        "id": snap.id,
        "room_id": snap.room_id,
        "label": snap.label,
        "saved_by": snap.saved_by,
        "thumbnail": snap.thumbnail,
        "created_at": snap.created_at.isoformat() if snap.created_at else None,
    }


def _prune_snapshots(room_id: str, db: Session):
    """Keep only the latest MAX_SNAPSHOTS entries; always preserve manual saves."""
    all_snaps = (
        db.query(WhiteboardSnapshot)
        .filter_by(room_id=room_id)
        .order_by(WhiteboardSnapshot.created_at.desc())
        .all()
    )
    if len(all_snaps) > MAX_SNAPSHOTS:
        to_delete = all_snaps[MAX_SNAPSHOTS:]
        # Only prune auto-saves, never manual ones
        for s in to_delete:
            if s.label == "Auto-save":
                db.delete(s)
        db.commit()
