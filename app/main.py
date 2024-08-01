import random
import time

from fastapi import FastAPI, status, HTTPException
from pydantic import BaseModel
import psycopg
from psycopg.rows import dict_row


app = FastAPI()


class Post(BaseModel):
    title: str | None = "No Title"
    content: str | None = None
    published: bool | None = True
    id: int | None = None


while True:
    try:
        conn = psycopg.connect(host='localhost', dbname='fcc-fastapi', user='postgres', password='VdlBr6p5v6YaAI',
                               row_factory=dict_row)
        cursor = conn.cursor()
        print("Database connection was successful!")
        break
    except Exception as error:
        print("Connecting to database failed")
        print(error)
        time.sleep(1)

my_posts: list[Post] = []


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/posts")
async def get_posts():
    posts =cursor.execute("SELECT * FROM posts").fetchall()
    return {"data": {"posts": posts}}


@app.get("/posts/latest")
async def get_latest_post():
    try:
        post: Post = my_posts[-1]
    except IndexError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not fetch the latest post.",
        )

    return {"data": post}


@app.get("/posts/{post_id}")
async def get_post(post_id: int):
    post = cursor.execute("SELECT * FROM posts WHERE id = %s ", [post_id]).fetchone()
                          
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"post with id: {post_id} was not found.",
        )
        
    return {"data": post}


@app.post("/posts", status_code=status.HTTP_201_CREATED)
def create_posts(post: Post):
    cursor.execute("""
                    INSERT INTO posts (title, content, published) 
                    VALUES (%s, %s, %s) 
                    RETURNING *
                   """,
          (post.title, post.content, post.published))
    new_post = cursor.fetchone()
    conn.commit()
    return {"data": new_post}


@app.delete("/posts/{post_id}", status_code=status.HTTP_200_OK)
def delete_post(post_id: int):
    cursor.execute("DELETE FROM posts WHERE id = %s", [post_id])

    
    if not cursor.rowcount:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"post with id: {post_id} was not found.",
        )

    conn.commit()
    return {"message": f"Post with id: {post_id} was successfully deleted."}


@app.put("/posts/{post_id}")
async def update_put_post(post_id: int, post: Post):
    updated_post = cursor.execute("""UPDATE 
                                        posts
                                    SET
                                        title = %s,
                                        content = %s,
                                        published = %s
                                    WHERE
                                        id = %s
                                    RETURNING *
                        """,
                              [post.title, post.content, post.published, post_id]).fetchone()
    
    if not cursor.rowcount:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"post with id: {post_id} was not found.",
        )
    
    conn.commit()
    return {"message": f"Post with id: {post_id} was successfully updated.", "data": updated_post}


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
