from fastapi import FastAPI, status, HTTPException, Depends
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from . import models, schemas, utils
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


@app.get("/posts", response_model=list[schemas.PostResponse])
async def get_posts(db: Session = Depends(get_db)):
    posts = db.query(models.Post).all()
    return posts


@app.get("/posts/{post_id}", response_model=schemas.PostResponse)
async def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).get({"id": post_id})

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"post with id: {post_id} was not found.",
        )

    return post


@app.post(
    "/posts", status_code=status.HTTP_201_CREATED, response_model=schemas.PostResponse
)
def create_posts(post: schemas.PostCreate, db: Session = Depends(get_db)):
    new_post = models.Post(**post.model_dump())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


@app.delete("/posts/{post_id}", status_code=status.HTTP_200_OK)
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


@app.put("/posts/{post_id}", response_model=schemas.PostResponse)
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


@app.post("/users", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    is_existing_user = bool(
        db.query(models.User).filter(models.User.email == user.email).first()
    )
    if is_existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    hashed_password = utils.hash(user.password)
    user.password = hashed_password
    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.get("/users/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user: models.User | None = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id: {user_id} was not found.",
        )

    return user
