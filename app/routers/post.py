from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session

from app import schemas, models
from app.database import get_db

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get("/", response_model=list[schemas.PostResponse])
async def get_posts(db: Session = Depends(get_db)):
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
def create_posts(post: schemas.PostCreate, db: Session = Depends(get_db)):
    new_post = models.Post(**post.model_dump())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


@router.delete("/{post_id}", status_code=status.HTTP_200_OK)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id)

    if not post.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"post with id: {post_id} was not found.",
        )

    post.delete(synchronize_session=False)
    db.commit()

    return {"message": f"Post with id: {post_id} was successfully deleted."}


@router.put("/{post_id}", response_model=schemas.PostResponse)
async def update_put_post(
    post_id: int, post: schemas.PostCreate, db: Session = Depends(get_db)
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
