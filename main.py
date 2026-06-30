import os
import subprocess
import uuid
from typing import Annotated

import edge_tts
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

load_dotenv()

app = FastAPI(title="Video to GIF API")

os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
templates = Jinja2Templates(directory="templates")
API_TOKEN = os.getenv("TOKEN_API", "")

def verify_api_key(x_api_key: str | None) -> None:
    if not API_TOKEN:
        raise HTTPException(status_code=500, detail="TOKEN_API chưa được cấu hình")

    if x_api_key != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "api_token": API_TOKEN,
        },
    )


@app.post("/api/video-to-gif")
async def video_to_gif(
    file: UploadFile = File(...),
    width: Annotated[int, Form()] = 480,
    height: Annotated[int, Form()] = 320,
    fps: Annotated[int, Form()] = 8,
    start_time: Annotated[int, Form()] = 0,
    duration: Annotated[int | None, Form()] = None,
    x_api_key: str | None = Header(default=None),
):
    verify_api_key(x_api_key)

    if not file.filename or not file.filename.lower().endswith(".mp4"):
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Chỉ hỗ trợ file .mp4"},
        )

    file_id = str(uuid.uuid4())
    input_path = f"uploads/{file_id}.mp4"
    output_path = f"outputs/{file_id}.gif"

    with open(input_path, "wb") as f:
        f.write(await file.read())

    command = [
        "ffmpeg",
        "-y",
        "-ss",
        str(start_time),
        "-i",
        input_path,
        "-vf",
        f"fps={fps},scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}",
        output_path,
    ]

    if duration is not None:
        command[4:4] = ["-t", str(duration)]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Convert thất bại. Kiểm tra đã cài ffmpeg chưa.",
            },
        )

    return {
        "status": "success",
        "gif_url": f"/outputs/{file_id}.gif",
    }


@app.post("/api/text-to-audio")
async def text_to_audio(
    text: Annotated[str, Form(...)],
    voice: Annotated[str, Form()] = "vi-VN-HoaiMyNeural",
    x_api_key: str | None = Header(default=None),
):
    verify_api_key(x_api_key)

    if not text.strip():
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Text không được để trống"},
        )

    file_id = str(uuid.uuid4())
    output_path = f"outputs/{file_id}.mp3"

    try:
        communicate = edge_tts.Communicate(text=text, voice=voice)
        await communicate.save(output_path)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Tạo audio thất bại",
                "detail": str(e),
            },
        )

    return {
        "status": "success",
        "audio_url": f"/outputs/{file_id}.mp3",
        "voice": voice,
    }
