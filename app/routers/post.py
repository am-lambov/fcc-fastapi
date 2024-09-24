from typing import Optional

from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session

from app import schemas, models, oauth2
from app.database import get_db

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get("/", response_model=list[schemas.PostResponse])
async def get_posts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    posts = db.query(models.Post).all()
    return posts


@router.get("/{post_id}", response_model=schemas.PostResponse)
async def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).get({"id": post_id})

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"post with id: {post_id} was not found.",
        )

    return post


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=schemas.PostResponse
)
def create_posts(
    post: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    new_post = models.Post(**post.model_dump())
    new_post.author_id = current_user.id
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    post = fetch_post_from_db(db, post_id)
    check_permission_to_delete_post(current_user, post)
    delete_post_from_db(db, post_id)


def check_permission_to_delete_post(user, post):
    if not is_author(user, post):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can delete only your own posts.",
        )


def is_author(user, post) -> bool:
    return post.author_id == user.id


def delete_post_from_db(db, post_id):
    db.query(models.Post).filter(models.Post.id == post_id).delete(
        synchronize_session=False
    )
    db.commit()


def fetch_post_from_db(db, post_id) -> models.Post:
    post: Optional[models.Post] = (
        db.query(models.Post).filter(models.Post.id == post_id).first()
    )
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"post with id: {post_id} was not found.",
        )
    return post


@router.put("/{post_id}", response_model=schemas.PostResponse)
async def update_put_post(
    post_id: int,
    post: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    post_query = db.query(models.Post).filter(models.Post.id == post_id)

    if not post_query.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"post with id: {post_id} was not found.",
        )

    post_query.update(post.model_dump(), synchronize_session=False)
    db.commit()

    return post_query.first()
