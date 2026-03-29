from fastapi import FastAPI, UploadFile, File, Form
import shutil
import os
from fastapi.concurrency import run_in_threadpool
import requests 
from services.linkedin_service import run_linkedin_post
from services.linkedin_service import run_repost_latest_post
app = FastAPI()


@app.post("/post-to-group")
async def post_to_group(
    group_url: str = Form(...),
    content: str = Form(...),
    image: UploadFile = File(...)
):
    image_path = f"temp_{image.filename}"

    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    try:
        # 🔥 FIX: run blocking code in thread
        result = await run_in_threadpool(
            run_linkedin_post, group_url, content, image_path
        )
        return result

    finally:
        if os.path.exists(image_path):
            os.remove(image_path)

@app.post("/post-with-image-url-to-group")
async def post_with_image_url_to_group(
    group_url: str = Form(...),
    content: str = Form(...),
    image_url: str = Form(...)
):
    image_path = "temp_image.png" 

    # 🔥 Download image from URL
    response = requests.get(image_url)

    with open(image_path, "wb") as f:
        f.write(response.content)

    try:
        result = await run_in_threadpool(
            run_linkedin_post, group_url, content, image_path
        )
        return result

    finally:
        if os.path.exists(image_path):
            os.remove(image_path)


@app.post("/repost-latest-company-post")
async def repost_latest_company_post(
    company_posts_url: str = Form(...),
    group_url: str = Form(...)
):
    result = await run_in_threadpool(
        run_repost_latest_post,
        company_posts_url,
        group_url
    )

    return result

@app.get("/")
def home():
    return {"message": "LinkedIn API running 🚀"}