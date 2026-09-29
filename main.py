import os
import cv2
import numpy as np

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import Response, JSONResponse

app = FastAPI(
    title="Rakib AI 4K Upscaler",
    version="1.1.0"
)

MODEL_PATH = "models/ESPCN_x2.pb"
MAX_FILE_SIZE = 15 * 1024 * 1024
MAX_INPUT_SIZE = 2000

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


def enhance_before_ai(image):
    """
    Very light preprocessing.
    Avoids aggressive processing so ESPCN
    can work with the original details.
    """

    # Mild noise reduction
    denoised = cv2.fastNlMeansDenoisingColored(
        image,
        None,
        3,
        3,
        7,
        21
    )

    # Blend mostly original image with denoised version
    # to avoid losing small details.
    result = cv2.addWeighted(
        image,
        0.75,
        denoised,
        0.25,
        0
    )

    return result


def enhance_after_ai(image):
    """
    Lightweight post-processing:
    - local contrast
    - controlled sharpening
    """

    # LAB local contrast
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(
        clipLimit=1.15,
        tileGridSize=(8, 8)
    )

    l = clahe.apply(l)

    enhanced = cv2.merge((l, a, b))
    enhanced = cv2.cvtColor(
        enhanced,
        cv2.COLOR_LAB2BGR
    )

    # Controlled unsharp mask
    blur = cv2.GaussianBlur(
        enhanced,
        (0, 0),
        1.0
    )

    sharpened = cv2.addWeighted(
        enhanced,
        1.12,
        blur,
        -0.12,
        0
    )

    # Keep values valid
    return np.clip(
        sharpened,
        0,
        255
    ).astype(np.uint8)


@app.get("/")
def home():
    return {
        "success": True,
        "name": "Rakib AI 4K Upscaler",
        "version": "1.1.0",
        "status": "running 🚀",
        "model": "ESPCN x2",
        "enhancement": True,
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
    try:
        if not image.content_type:
            raise HTTPException(
                status_code=400,
                detail="Missing content type"
            )

        if not image.content_type.startswith("image/"):
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

        if len(data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Image too large. Maximum 15 MB."
            )

        # Decode
        img_array = np.frombuffer(
            data,
            dtype=np.uint8
        )

        original = cv2.imdecode(
            img_array,
            cv2.IMREAD_COLOR
        )

        if original is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid image"
            )

        original_h, original_w = original.shape[:2]

        image = original.copy()

        # Keep Render Free CPU/RAM usage reasonable
        if max(original_w, original_h) > MAX_INPUT_SIZE:

            ratio = (
                MAX_INPUT_SIZE /
                max(original_w, original_h)
            )

            new_w = max(
                1,
                int(original_w * ratio)
            )

            new_h = max(
                1,
                int(original_h * ratio)
            )

            image = cv2.resize(
                image,
                (new_w, new_h),
                interpolation=cv2.INTER_AREA
            )

        # --------------------------------
        # 1. LIGHT PRE-ENHANCEMENT
        # --------------------------------

        image = enhance_before_ai(image)

        # --------------------------------
        # 2. ESPCN AI SUPER RESOLUTION
        # --------------------------------

        result = sr.upsample(image)

        # --------------------------------
        # 3. LIGHT POST-ENHANCEMENT
        # --------------------------------

        result = enhance_after_ai(result)

        # --------------------------------
        # 4. MAX 4K OUTPUT
        # --------------------------------

        h, w = result.shape[:2]

        max_w = 3840
        max_h = 2160

        if w > max_w or h > max_h:

            ratio = min(
                max_w / w,
                max_h / h
            )

            output_w = max(
                1,
                int(w * ratio)
            )

            output_h = max(
                1,
                int(h * ratio)
            )

            result = cv2.resize(
                result,
                (output_w, output_h),
                interpolation=cv2.INTER_LANCZOS4
            )

        final_h, final_w = result.shape[:2]

        # --------------------------------
        # 5. HIGH QUALITY JPEG
        # --------------------------------

        success, encoded = cv2.imencode(
            ".jpg",
            result,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                96
            ]
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to encode output"
            )

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
                    "ESPCN-x2",

                "X-Enhancement":
                    "denoise+contrast+sharpen"
            }
        )

    except HTTPException:
        raise

    except Exception as error:
        print("UPSCALE ERROR:", error)

        raise HTTPException(
            status_code=500,
            detail=str(error)
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
