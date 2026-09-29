# 🚀 Rakib AI 4K Upscaler

A lightweight AI image upscaling API powered by ESPCN x2 Super Resolution.

Unlike a normal resize API, this project uses an AI super-resolution model with lightweight enhancement for better sharpness, contrast, and clarity.

## ✨ Features

- ESPCN x2 AI Super Resolution
- AI-based 2x upscaling
- Lightweight image enhancement
- Noise reduction
- Contrast enhancement
- Controlled sharpening
- JPG, PNG and WebP support
- High-quality JPEG output
- FastAPI based
- CPU friendly
- Render Free compatible
- No API key required
- Maximum upload size: 15 MB
- Up to 4K output dimensions

## 🧠 Processing

Input Image
    ↓
Light Noise Reduction
    ↓
ESPCN x2 AI Super Resolution
    ↓
Contrast Enhancement
    ↓
Controlled Sharpening
    ↓
4K Size Limit
    ↓
High Quality JPEG

## 🛠️ Tech Stack

- Python
- FastAPI
- OpenCV
- OpenCV DNN Super Resolution
- ESPCN
- NumPy
- Pillow
- Uvicorn

## 📁 Project Structure

rakib-4k-api/
 main.py
 requirements.txt
 render.yaml
 README.md
 models/
    └── ESPCN_x2.pb

## ⚡ Run Locally

### Clone

git clone https://github.com/bdrakib123/rakib-4k-api.git
cd rakib-4k-api

### Create Virtual Environment

python3 -m venv venv

### Activate

Linux / Debian / Termux:

source venv/bin/activate

Windows:

venv\Scripts\activate

### Install Dependencies

pip install -r requirements.txt

### Start Server

uvicorn main:app --host 0.0.0.0 --port 3000

API:
http://127.0.0.1:3000

## 🔍 API Endpoints

### GET /

Returns API information.

curl http://127.0.0.1:3000/

Example response:

{
  "success": true,
  "name": "Rakib AI 4K Upscaler",
  "version": "1.1.0",
  "status": "running",
  "model": "ESPCN x2",
  "enhancement": true,
  "endpoint": "POST /api/upscale"
}

### GET /health

Checks API and model status.

curl http://127.0.0.1:3000/health

Example response:

{
  "success": true,
  "status": "ok",
  "model_loaded": true
}

## 🖼️ Upscale Image

### POST /api/upscale

Upload an image using multipart/form-data.

Field name:

image

Example:

curl -X POST \
  -F "image=@image.jpg" \
  http://127.0.0.1:3000/api/upscale \
  --output result.jpg

The API returns the enhanced image directly as image/jpeg.

## 📊 Response Headers

The API returns:

X-Original-Size
X-Output-Size
X-Model
X-Enhancement

Example:

X-Original-Size: 618x608
X-Output-Size: 1236x1216
X-Model: ESPCN-x2
X-Enhancement: denoise+contrast+sharpen

## 📈 Example

Input:
618 × 608

Output:
1236 × 1216

Processing:

ESPCN x2
+
Denoise
+
Contrast Enhancement
+
Controlled Sharpening

## ☁️ Deploy on Render

This project is designed to work with Render.

Build Command:

pip install -r requirements.txt

Start Command:

uvicorn main:app --host 0.0.0.0 --port $PORT

Health Check:

/health

The repository includes render.yaml.

## ⚙️ Render Configuration

services:
  - type: web
    name: rakib-4k-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: PYTHON_VERSION
        value: 3.13.5

## ⚠️ Limitations

This project is designed to be lightweight and CPU-friendly.

It is not a replacement for large super-resolution models such as Real-ESRGAN.

ESPCN can reconstruct and enhance some details during super-resolution, but it cannot perfectly recover information that was completely lost from the original image.

Large images may require more processing time on CPU-based hosting.

Maximum upload size:
15 MB

## 🔐 Security

The API does not require an API key by default.

If you expose this API publicly, consider adding:

- API key authentication
- Rate limiting
- Request limits
- Abuse protection

## 📜 License

MIT License

## 👨‍💻 Author

Rakib

Built with ❤️ using Python, FastAPI and OpenCV.

## ⭐ Support

If this project is useful to you, consider giving the repository a ⭐ on GitHub.
