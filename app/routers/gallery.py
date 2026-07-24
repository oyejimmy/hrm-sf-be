"""
Gallery router — HR creates albums & uploads images; employees view & download.

Endpoints:
  GET    /api/gallery/albums              – list published albums
  POST   /api/gallery/albums              – HR creates album
  GET    /api/gallery/albums/{id}         – album detail with images
  PUT    /api/gallery/albums/{id}         – HR updates album metadata
  DELETE /api/gallery/albums/{id}         – HR deletes album (cascades images)

  POST   /api/gallery/albums/{id}/images  – HR uploads images (bulk)
  DELETE /api/gallery/images/{id}         – HR deletes a single image

  GET    /api/gallery/celebrations        – active celebration broadcasts
  POST   /api/gallery/celebrations        – HR creates a broadcast
  PUT    /api/gallery/celebrations/{id}   – HR updates a broadcast
  DELETE /api/gallery/celebrations/{id}   – HR removes a broadcast
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_role
from ..database import get_db
from ..models.gallery import CelebrationBroadcast, GalleryAlbum, GalleryImage
from ..models.user import User
from ..schemas.gallery import (
    AlbumCreate,
    AlbumDetailResponse,
    AlbumResponse,
    AlbumUpdate,
    BulkImageUpload,
    CelebrationCreate,
    CelebrationResponse,
    ImageResponse,
)

router = APIRouter(prefix="/api/gallery", tags=["gallery"])


# ─── helpers ─────────────────────────────────────────────────────────────────

def _album_to_dict(album: GalleryAlbum, include_images: bool = False) -> dict:
    d = {
        "id": album.id,
        "title": album.title,
        "description": album.description,
        "cover_image": album.cover_image,
        "is_published": album.is_published,
        "created_by": album.created_by,
        "created_at": album.created_at,
        "image_count": len(album.images),
    }
    if include_images:
        d["images"] = [
            {
                "id": img.id,
                "album_id": img.album_id,
                "title": img.title,
                "file_name": img.file_name,
                "file_url": img.file_url,
                "file_size": img.file_size,
                "mime_type": img.mime_type,
                "uploaded_by": img.uploaded_by,
                "created_at": img.created_at,
            }
            for img in album.images
        ]
    return d


def _celebration_to_dict(cel: CelebrationBroadcast) -> dict:
    emp = cel.subject_employee
    user = emp.user if emp else None
    award = cel.award
    return {
        "id": cel.id,
        "broadcast_type": cel.broadcast_type,
        "title": cel.title,
        "message": cel.message,
        "subject_employee_id": cel.subject_employee_id,
        "award_id": cel.award_id,
        "event_date": cel.event_date,
        "expires_at": cel.expires_at,
        "is_active": cel.is_active,
        "created_by": cel.created_by,
        "created_at": cel.created_at,
        "subject_name": f"{user.first_name} {user.last_name}" if user else None,
        "subject_avatar": emp.avatar_url if emp else None,
        "subject_position": emp.position if emp else None,
        "award_type": award.award_type if award else None,
    }


# ─── Albums ──────────────────────────────────────────────────────────────────

@router.get("/albums", response_model=List[AlbumResponse])
def list_albums(
    published_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(GalleryAlbum)
    # Non-HR users only see published albums
    if current_user.role not in ("admin", "hr"):
        q = q.filter(GalleryAlbum.is_published == True)  # noqa: E712
    elif published_only:
        q = q.filter(GalleryAlbum.is_published == True)  # noqa: E712

    albums = q.order_by(GalleryAlbum.created_at.desc()).all()
    return [_album_to_dict(a) for a in albums]


@router.post("/albums", response_model=AlbumResponse)
def create_album(
    body: AlbumCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    album = GalleryAlbum(
        title=body.title,
        description=body.description,
        is_published=body.is_published,
        created_by=current_user.id,
    )
    db.add(album)
    db.commit()
    db.refresh(album)
    return _album_to_dict(album)


@router.get("/albums/{album_id}", response_model=AlbumDetailResponse)
def get_album(
    album_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    album = db.query(GalleryAlbum).filter(GalleryAlbum.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    if not album.is_published and current_user.role not in ("admin", "hr"):
        raise HTTPException(status_code=403, detail="Album not available")

    return _album_to_dict(album, include_images=True)


@router.put("/albums/{album_id}", response_model=AlbumResponse)
def update_album(
    album_id: int,
    body: AlbumUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    album = db.query(GalleryAlbum).filter(GalleryAlbum.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    if body.title is not None:
        album.title = body.title
    if body.description is not None:
        album.description = body.description
    if body.is_published is not None:
        album.is_published = body.is_published

    db.commit()
    db.refresh(album)
    return _album_to_dict(album)


@router.delete("/albums/{album_id}")
def delete_album(
    album_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    album = db.query(GalleryAlbum).filter(GalleryAlbum.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    db.delete(album)
    db.commit()
    return {"message": "Album deleted"}


# ─── Images ──────────────────────────────────────────────────────────────────

@router.post("/albums/{album_id}/images", response_model=List[ImageResponse])
def upload_images(
    album_id: int,
    body: BulkImageUpload,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    album = db.query(GalleryAlbum).filter(GalleryAlbum.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    created = []
    for img_data in body.images:
        img = GalleryImage(
            album_id=album_id,
            title=img_data.title,
            file_name=img_data.file_name,
            file_url=img_data.file_url,
            file_size=img_data.file_size,
            mime_type=img_data.mime_type,
            uploaded_by=current_user.id,
        )
        db.add(img)
        db.flush()
        created.append(img)

    # Set first image as cover if album has no cover yet
    if not album.cover_image and created:
        album.cover_image = created[0].file_url

    db.commit()
    for img in created:
        db.refresh(img)

    return created


@router.delete("/images/{image_id}")
def delete_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    img = db.query(GalleryImage).filter(GalleryImage.id == image_id).first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")

    # Update album cover if this was the cover
    album = db.query(GalleryAlbum).filter(GalleryAlbum.id == img.album_id).first()
    if album and album.cover_image == img.file_url:
        remaining = (
            db.query(GalleryImage)
            .filter(GalleryImage.album_id == img.album_id, GalleryImage.id != image_id)
            .first()
        )
        album.cover_image = remaining.file_url if remaining else None

    db.delete(img)
    db.commit()
    return {"message": "Image deleted"}


# ─── Celebrations ────────────────────────────────────────────────────────────

@router.get("/celebrations", response_model=List[CelebrationResponse])
def list_celebrations(
    broadcast_type: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(CelebrationBroadcast)
    if active_only:
        now = datetime.utcnow()
        q = q.filter(
            CelebrationBroadcast.is_active == True,  # noqa: E712
            (CelebrationBroadcast.expires_at == None) | (CelebrationBroadcast.expires_at >= now),  # noqa: E711
        )
    if broadcast_type:
        q = q.filter(CelebrationBroadcast.broadcast_type == broadcast_type)

    cels = q.order_by(CelebrationBroadcast.event_date.desc()).all()
    return [_celebration_to_dict(c) for c in cels]


@router.post("/celebrations", response_model=CelebrationResponse)
def create_celebration(
    body: CelebrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    cel = CelebrationBroadcast(
        broadcast_type=body.broadcast_type,
        title=body.title,
        message=body.message,
        subject_employee_id=body.subject_employee_id,
        award_id=body.award_id,
        event_date=body.event_date,
        expires_at=body.expires_at,
        created_by=current_user.id,
    )
    db.add(cel)
    db.commit()
    db.refresh(cel)
    return _celebration_to_dict(cel)


@router.put("/celebrations/{cel_id}", response_model=CelebrationResponse)
def update_celebration(
    cel_id: int,
    body: CelebrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    cel = db.query(CelebrationBroadcast).filter(CelebrationBroadcast.id == cel_id).first()
    if not cel:
        raise HTTPException(status_code=404, detail="Celebration not found")

    cel.broadcast_type = body.broadcast_type
    cel.title = body.title
    cel.message = body.message
    cel.subject_employee_id = body.subject_employee_id
    cel.award_id = body.award_id
    cel.event_date = body.event_date
    cel.expires_at = body.expires_at
    db.commit()
    db.refresh(cel)
    return _celebration_to_dict(cel)


@router.delete("/celebrations/{cel_id}")
def delete_celebration(
    cel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    cel = db.query(CelebrationBroadcast).filter(CelebrationBroadcast.id == cel_id).first()
    if not cel:
        raise HTTPException(status_code=404, detail="Celebration not found")
    db.delete(cel)
    db.commit()
    return {"message": "Celebration deleted"}
