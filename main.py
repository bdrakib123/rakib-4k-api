import os
import cv2
import numpy as np

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import Response, JSONResponse

app = FastAPI(
    title="Rakib AI 4K Upscaler",
    version="1.0.0"
)

MODEL_PATH = "models/ESPCN_x2.pb"

sr = None


def load_model():
    global sr

    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(
            f"Model not found: {MODEL_PATH}"
        )

    sr = cv2.dnn_superres.DnnSuperResImpl_create()
    sr.readModel(MODEL_PATH)
    sr.setModel("espcn", 2)

    print("✅ ESPCN x2 model loaded")


@app.on_event("startup")
def startup():
    load_model()


@app.get("/")
def home():
    return {
        "success": True,
        "name": "Rakib AI 4K Upscaler",
        "version": "1.0.0",
        "status": "running 🚀",
        "model": "ESPCN x2",
        "endpoint": "POST /api/upscale"
    }


@app.get("/health")
def health():
    return {
        "success": True,
        "status": "ok",
        "model_loaded": sr is not None
    }


@app.post("/api/upscale")
async def upscale(
    image: UploadFile = File(...)
):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Only image files are allowed"
        )

    data = await image.read()

    if not data:
        raise HTTPException(
            status_code=400,
            detail="Empty image"
        )

    # 15 MB limit
    if len(data) > 15 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Image too large. Maximum 15 MB."
        )

    # Decode image
    img_array = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid image"
        )

    original_h, original_w = image.shape[:2]

    # Avoid extremely large inputs on Render Free
    max_input = 2000

    if max(original_w, original_h) > max_input:
        ratio = max_input / max(original_w, original_h)

        new_w = int(original_w * ratio)
        new_h = int(original_h * ratio)

        image = cv2.resize(
            image,
            (new_w, new_h),
            interpolation=cv2.INTER_AREA
        )

    # AI Super Resolution x2
    result = sr.upsample(image)

    # Mild final sharpening
    blur = cv2.GaussianBlur(
        result,
        (0, 0),
        1.0
    )

    result = cv2.addWeighted(
        result,
        1.15,
        blur,
        -0.15,
        0
    )

    # Keep output within 4K
    h, w = result.shape[:2]

    max_w = 3840
    max_h = 2160

    if w > max_w or h > max_h:
        ratio = min(
            max_w / w,
            max_h / h
        )

        w2 = int(w * ratio)
        h2 = int(h * ratio)

        result = cv2.resize(
            result,
            (w2, h2),
            interpolation=cv2.INTER_LANCZOS4
        )

    # Encode JPG
    success, encoded = cv2.imencode(
        ".jpg",
        result,
        [
            cv2.IMWRITE_JPEG_QUALITY,
            95
        ]
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to encode output"
        )

    final_h, final_w = result.shape[:2]

    return Response(
        content=encoded.tobytes(),
        media_type="image/jpeg",
        headers={
            "Content-Disposition":
                'inline; filename="4k-enhanced.jpg"',
            "X-Original-Size":
                f"{original_w}x{original_h}",
            "X-Output-Size":
                f"{final_w}x{final_h}",
            "X-Model":
                "ESPCN-x2"
        }
    )


@app.exception_handler(Exception)
async def general_error(request, exc):
    print("ERROR:", exc)

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc)
        }
    )
