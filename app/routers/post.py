from typing import Optional, Type

from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session

from app import schemas, oauth2
from app.models import User, Post
from app.database import get_db

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get("/", response_model=list[schemas.PostResponse])
async def get_posts(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
    limit: int = 10, skip: int = 0, search: str = ""
):
    posts: Optional[list[Type[Post]]] = db.query(Post).filter(Post.title.contains(search)).limit(limit).offset(skip).all()
    return posts


@router.get("/{post_id}", response_model=schemas.PostResponse)
async def get_post(post_id: int, db: Session = Depends(get_db)):
    post: Post = fetch_post_from_db(db, post_id)
    return post


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=schemas.PostResponse
)
def create_posts(
    post: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    new_post: Post = Post(**post.model_dump())
    new_post.author_id = current_user.id
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    post: Post = fetch_post_from_db(db, post_id)
    check_permission_to_edit_post(current_user, post)
    delete_post_from_db(db, post_id)


def check_permission_to_edit_post(user: User, post: Post) -> None:
    if not is_author(user, post):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can update/delete only your own posts.",
        )


def is_author(user: User, post: Post) -> bool:
    return post.author_id == user.id


def delete_post_from_db(db: Session, post_id: int) -> None:
    db.query(Post).filter(Post.id == post_id).delete(synchronize_session=False)
    db.commit()


def fetch_post_from_db(db: Session, post_id: int) -> Post:
    post: Optional[Post] = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"post with id: {post_id} was not found.",
        )
    return post


@router.put("/{post_id}", response_model=schemas.PostResponse)
async def update_put_post(
    post_id: int,
    updated_post: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    old_post = fetch_post_from_db(db, post_id)
    check_permission_to_edit_post(current_user, old_post)
    await update_post(db, updated_post, post_id)

    return fetch_post_from_db(db, post_id)


async def update_post(db, post, post_id):
    db.query(Post).filter(Post.id == post_id).update(
        post.model_dump(), synchronize_session=False
    )
    db.commit()
