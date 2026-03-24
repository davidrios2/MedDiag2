"""
Audio endpoints — upload, list, detail, delete.
"""

import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models import User, UserRole
from app.schemas.audio import AudioListResponse, AudioRecordOut, AudioUploadResponse
from app.services.auth_service import get_current_user, get_db
from app.services import audio_service

router = APIRouter(prefix="/audio", tags=["audio"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_admin(db: Session, user: User) -> bool:
    return any(
        ur.role.code == "admin"
        for ur in db.query(UserRole).filter(UserRole.user_id == user.id).all()
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=AudioUploadResponse, status_code=201)
async def upload_audio(
    file: UploadFile = File(...),
    source_type: str = Form("upload"),
    language_code: str | None = Form(None),
    notes: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload an audio file.
    Accepts multipart/form-data with the audio file and optional metadata.
    """
    # Read the file content to measure size
    contents = await file.read()
    file_size = len(contents)

    # Validate
    try:
        audio_service.validate_audio_file(file.content_type, file_size)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Reset file cursor for storage
    import io
    file_like = io.BytesIO(contents)

    # Save to storage
    file_meta = audio_service.save_audio_file(
        file=file_like,
        user_id=current_user.id,
        original_filename=file.filename or "audio.bin",
        content_type=file.content_type,
    )

    # Persist metadata in DB
    record = audio_service.create_audio_record(
        db=db,
        user_id=current_user.id,
        file_meta=file_meta,
        original_filename=file.filename or "audio.bin",
        content_type=file.content_type,
        file_size=file_size,
        source_type=source_type,
        language_code=language_code,
        notes=notes,
    )
    db.commit()

    return AudioUploadResponse(
        audio_id=record.id,
        uuid=record.uuid,
        status=record.status,
        original_filename=record.original_filename,
        mime_type=record.mime_type,
        file_size_bytes=record.file_size_bytes,
        created_at=record.created_at,
    )


@router.get("/me", response_model=AudioListResponse)
def list_my_audios(
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List audio records for the authenticated user."""
    items, total = audio_service.list_user_audios(
        db, current_user.id, status_filter=status_filter, limit=limit, offset=offset
    )
    return AudioListResponse(
        items=[AudioRecordOut.model_validate(i) for i in items],
        total=total,
    )


@router.get("/{audio_id}", response_model=AudioRecordOut)
def get_audio(
    audio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single audio record. Owner or admin only."""
    record = audio_service.get_audio_record(db, audio_id)
    if not record:
        raise HTTPException(status_code=404, detail="Audio record not found.")

    if record.user_id != current_user.id and not _is_admin(db, current_user):
        raise HTTPException(status_code=403, detail="Access denied.")

    return AudioRecordOut.model_validate(record)


@router.delete("/{audio_id}", status_code=204)
def delete_audio(
    audio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft-delete an audio record. Owner or admin only."""
    record = audio_service.get_audio_record(db, audio_id)
    if not record:
        raise HTTPException(status_code=404, detail="Audio record not found.")

    if record.user_id != current_user.id and not _is_admin(db, current_user):
        raise HTTPException(status_code=403, detail="Access denied.")

    audio_service.soft_delete_audio(db, record)
    db.commit()
