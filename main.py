import random

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Post(BaseModel):
    title: str
    content: str | None = None
    rating: int | None = None
    published: bool | None = True
    id: int | None = None


my_posts: list[Post] = []


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/posts")
async def get_posts():
    return {"data": {"posts": my_posts}}


@app.get("/posts/latest")
async def get_latest_post():
    post: Post = my_posts[-1]
    return {"data": post}


@app.get("/posts/{post_id}")
async def get_post(post_id: int):
    post = fetch_post(post_id)
    return {"message": f"Here is post {post_id}", "data": post}


@app.post("/posts")
def create_posts(post: Post):
    post.id = get_random_id()
    my_posts.append(post)
    return {"data": post}


def fetch_post(post_id: int):
    for post in my_posts:
        if post.id == post_id:
            return post


def get_random_id():
    existing_ids = [post.id for post in my_posts]
    while True:
        rid = random.randint(1, 5)
        if rid not in existing_ids:
            return rid
