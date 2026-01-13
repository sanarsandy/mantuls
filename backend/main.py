"""
OCR Service API - FastAPI Application with API Key Authentication
"""
import uuid
import logging
from typing import Dict, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query, Header, Depends, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


from providers import get_provider, list_providers, get_provider_names
from config import (
    load_config, save_config, get_active_provider, 
    get_provider_config, set_active_provider, update_provider_config
)
from api_keys import (
    create_api_key, validate_api_key, list_api_keys, 
    revoke_api_key, delete_api_key, is_auth_enabled, set_auth_enabled,
    update_api_key, get_api_key_by_id, increment_usage
)
from auth_tokens import generate_frontend_token, verify_frontend_token
from sso_auth import sso_login, generate_jwt_token, verify_jwt_token


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tools Imports
try:
    from app_tools.pdf_tools import merge_pdfs, split_pdf, compress_pdf, add_watermark
    from app_tools.pdf_converter import pdf_to_word, word_to_pdf
    from app_tools.image_tools import convert_image
    from app_tools.qr_tools import generate_qr
    from app_tools.security_tools import protect_pdf, unlock_pdf
except ImportError as e:
    logger.error(f"CRITICAL ERROR: Failed to import standard tools: {e}")

# AI Tools Imports (Risky)
try:
    from app_tools.image_magic import remove_background
except ImportError as e:
    logger.error(f"WARNING: Failed to import AI tools (image_magic): {e}")
    # Define a dummy function to prevent NameError in endpoint
    def remove_background(*args, **kwargs):
        raise ImportError("AI tools are not available. Check server logs.")

# ... (existing code)



# ... (existing code)



# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate Limiter - uses IP address by default
def get_rate_limit_key(request: Request) -> str:
    """Get rate limit key from API key header or IP"""
    api_key_id = request.headers.get("X-API-Key-ID", "")
    api_key = request.headers.get("X-API-Key", "")
    if api_key_id:
        return f"key:{api_key_id}"
    if api_key:
        return f"apikey:{api_key[:20]}"
    return get_remote_address(request)

limiter = Limiter(key_func=get_rate_limit_key)

app = FastAPI(title="OCR Service API", version="2.2.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key Security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# In-memory storage for tasks (Replace with Redis/Database for production)
tasks_db: Dict[str, dict] = {}


# ============== Startup Events ==============

@app.on_event("startup")
async def startup_event():
    """Pre-load PaddleOCR model on startup for faster first request"""
    logger.info("Pre-loading PaddleOCR model...")
    try:
        from providers import get_provider
        paddle_provider = get_provider("paddle_ocr")
        # Warm up the model by calling _get_engine
        paddle_provider._get_engine({"lang": "latin"})
        logger.info("PaddleOCR model pre-loaded successfully!")
    except Exception as e:
        logger.warning(f"Failed to pre-load PaddleOCR: {e}")


# ============== Models ==============

class TaskResponse(BaseModel):
    task_id: str
    status: str

class SettingsUpdate(BaseModel):
    active_provider: Optional[str] = None
    providers: Optional[Dict] = None

class APIKeyCreate(BaseModel):
    name: str
    description: Optional[str] = ""

class APIKeyAuthToggle(BaseModel):
    enabled: bool

class APIKeyUpdate(BaseModel):
    custom_prompt: Optional[str] = None
    output_format: Optional[str] = None
    description: Optional[str] = None
    provider: Optional[str] = None


# ============== Auth Dependency ==============

async def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    x_api_key_id: Optional[str] = Header(None, alias="X-API-Key-ID")
):
    """
    Verify API key for protected endpoints
    Accepts either:
    - X-API-Key: the actual API key (for external apps)
    - X-API-Key-ID: the key ID (for internal frontend testing)
    """
    # Skip auth if disabled
    if not is_auth_enabled():
        # Even if auth disabled, check for key ID to get custom prompt
        if x_api_key_id:
            key_data = get_api_key_by_id(x_api_key_id)
            if key_data:
                return key_data
        return {"name": "auth_disabled", "custom_prompt": "", "output_format": "text"}
    
    # Check for signed token first (secure frontend auth)
    if x_api_key_id:
        # Try to verify as signed token
        is_valid, key_id = verify_frontend_token(x_api_key_id)
        if is_valid and key_id:
            key_data = get_api_key_by_id(key_id)
            if key_data and key_data.get("is_active"):
                return key_data
        # Fallback to raw ID for backwards compatibility (will be deprecated)
        key_data = get_api_key_by_id(x_api_key_id)
        if key_data and key_data.get("is_active"):
            logger.warning(f"Using raw key ID - should migrate to signed tokens")
            return key_data
        raise HTTPException(status_code=401, detail="Invalid token or API key ID")
    
    # Check for actual API key (external apps)
    if not x_api_key:
        raise HTTPException(
            status_code=401, 
            detail="API key required. Pass via X-API-Key header."
        )
    
    # Validate key
    key_data = validate_api_key(x_api_key)
    if not key_data:
        raise HTTPException(
            status_code=401, 
            detail="Invalid or revoked API key"
        )
    
    return key_data


# ============== Root ==============

@app.get("/")
def read_root():
    return {"message": "OCR Service is running", "version": "2.1.0"}


# ============== SSO Authentication ==============

class SSOLoginRequest(BaseModel):
    user: str  # Email or NIP/NPP
    password: str

class SSOLoginResponse(BaseModel):
    success: bool
    message: str
    user: Optional[Dict] = None

@app.post("/api/v1/auth/login")
def login_sso(credentials: SSOLoginRequest):
    """
    Authenticate user via LMAN SSO.
    Returns user data on success.
    """
    if not credentials.user or not credentials.password:
        raise HTTPException(status_code=400, detail="Email/NIP and password are required")
    
    user_data = sso_login(credentials.user, credentials.password)
    
    if user_data:
        # Generate JWT token
        token = generate_jwt_token(user_data)
        
        # Return user data with token
        safe_user = {
            "email": user_data.get("email"),
            "name": user_data.get("name"),
            "nip": user_data.get("nip_npp"),
            "is_admin": bool(user_data.get("is_admin", 0)),
            "status": user_data.get("status")
        }
        return {
            "success": True,
            "message": "Login successful",
            "token": token,
            "user": safe_user
        }
    else:
        raise HTTPException(
            status_code=401, 
            detail="Invalid credentials. Please check your email/NIP and password."
        )


# ============== API Key Management ==============

@app.get("/api/v1/auth/keys")
def get_api_keys():
    """List all API keys (admin only - no auth check for now)"""
    return {
        "keys": list_api_keys(),
        "auth_enabled": is_auth_enabled()
    }


@app.post("/api/v1/auth/keys")
def create_new_api_key(key_data: APIKeyCreate):
    """Create a new API key"""
    result = create_api_key(key_data.name, key_data.description)
    # Generate signed token for frontend use
    frontend_token = generate_frontend_token(result["id"])
    return {
        "message": "API key created. Save this key - it won't be shown again!",
        "key": result,
        "frontend_token": frontend_token
    }


@app.delete("/api/v1/auth/keys/{key_id}")
def delete_existing_api_key(key_id: str):
    """Delete an API key"""
    if delete_api_key(key_id):
        return {"message": "API key deleted"}
    raise HTTPException(status_code=404, detail="API key not found")


@app.post("/api/v1/auth/keys/{key_id}/revoke")
def revoke_existing_api_key(key_id: str):
    """Revoke (deactivate) an API key"""
    if revoke_api_key(key_id):
        return {"message": "API key revoked"}
    raise HTTPException(status_code=404, detail="API key not found")


@app.put("/api/v1/auth/toggle")
def toggle_api_auth(data: APIKeyAuthToggle):
    """Enable or disable API key authentication"""
    set_auth_enabled(data.enabled)
    return {"auth_enabled": data.enabled}


@app.get("/api/v1/auth/keys/{key_id}")
def get_single_api_key(key_id: str):
    """Get a single API key by ID"""
    key = get_api_key_by_id(key_id)
    if key:
        return {"key": key}
    raise HTTPException(status_code=404, detail="API key not found")


@app.post("/api/v1/auth/keys/{key_id}/token")
def generate_token_for_key(key_id: str):
    """Generate a signed frontend token for an API key"""
    key = get_api_key_by_id(key_id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    if not key.get("is_active"):
        raise HTTPException(status_code=400, detail="API key is not active")
    
    token = generate_frontend_token(key_id)
    return {
        "key_id": key_id,
        "frontend_token": token,
        "valid_for_seconds": 3600
    }


@app.put("/api/v1/auth/keys/{key_id}")
def update_existing_api_key(key_id: str, data: APIKeyUpdate):
    """Update an API key's custom prompt and settings"""
    updates = {}
    if data.custom_prompt is not None:
        updates["custom_prompt"] = data.custom_prompt
    if data.output_format is not None:
        updates["output_format"] = data.output_format
    if data.description is not None:
        updates["description"] = data.description
    if data.provider is not None:
        updates["provider"] = data.provider
    
    if update_api_key(key_id, updates):
        return {"message": "API key updated", "key": get_api_key_by_id(key_id)}
    raise HTTPException(status_code=404, detail="API key not found")


# ============== Settings API ==============

@app.get("/api/v1/settings")
def get_settings():
    """Get current OCR settings"""
    config = load_config()
    available_providers = list_providers()
    return {
        "active_provider": config.get("active_provider", "paddle_ocr"),
        "providers": config.get("providers", {}),
        "available_providers": available_providers
    }


@app.put("/api/v1/settings")
def update_settings(settings: SettingsUpdate):
    """Update OCR settings"""
    config = load_config()
    
    if settings.active_provider:
        if settings.active_provider not in get_provider_names():
            raise HTTPException(status_code=400, detail=f"Unknown provider: {settings.active_provider}")
        config["active_provider"] = settings.active_provider
    
    if settings.providers:
        for name, provider_config in settings.providers.items():
            if "providers" not in config:
                config["providers"] = {}
            config["providers"][name] = provider_config
    
    if save_config(config):
        return {"status": "success", "config": config}
    else:
        raise HTTPException(status_code=500, detail="Failed to save configuration")


@app.get("/api/v1/providers")
def list_available_providers():
    """List all available OCR providers"""
    return {"providers": list_providers()}


# ============== OCR API (Protected) ==============

def process_ocr_task(task_id: str, file_bytes: bytes, provider_name: str, custom_prompt: str = ""):
    """Background task for OCR processing with multi-page PDF support"""
    from utils.image import is_pdf, load_pdf_pages, load_image_from_bytes, preprocess_for_ocr
    import cv2
    
    tasks_db[task_id]["status"] = "processing"
    try:
        provider = get_provider(provider_name)
        provider_config = get_provider_config(provider_name).copy()
        
        # Merge custom prompt from API key if provided
        if custom_prompt:
            provider_config["prompt"] = custom_prompt
        
        # Check if file is a multi-page PDF
        if is_pdf(file_bytes):
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            logger.info(f"Task {task_id}: Processing multi-page PDF...")
            pages = load_pdf_pages(file_bytes, dpi=200)
            total_pages = len(pages)
            
            tasks_db[task_id]["status"] = f"processing {total_pages} pages in parallel"
            
            # Function to process a single page
            def process_single_page(page_data):
                page_num, page_img = page_data
                _, buffer = cv2.imencode('.png', page_img)
                page_bytes = buffer.tobytes()
                result = provider.process(page_bytes, provider_config)
                return page_num, result
            
            # Process pages in parallel (max 4 workers to avoid memory overload)
            all_results = [None] * total_pages
            max_workers = min(4, total_pages)
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(process_single_page, (i, page_img)): i
                    for i, page_img in enumerate(pages)
                }
                
                completed = 0
                for future in as_completed(futures):
                    page_num, result = future.result()
                    all_results[page_num] = result
                    completed += 1
                    tasks_db[task_id]["status"] = f"processed {completed}/{total_pages} pages"
                    logger.info(f"Task {task_id}: Completed page {page_num + 1}")
            
            # Combine all results in order
            all_text = []
            all_details = []
            for i, result in enumerate(all_results):
                if result and result.raw_text:
                    all_text.append(f"--- Page {i+1} ---\n{result.raw_text}")
                if result:
                    all_details.extend(result.details)
            
            # Combine all results
            combined_result = {
                "status": "success",
                "raw_text": "\n\n".join(all_text),
                "details": [d.to_dict() if hasattr(d, 'to_dict') else d for d in all_details],
                "provider": provider_name,
                "page_count": total_pages
            }
            
            tasks_db[task_id]["status"] = "completed"
            tasks_db[task_id]["result"] = combined_result
            logger.info(f"Task {task_id}: Completed {total_pages} pages (parallel)")
        else:
            # Single image processing (original behavior)
            result = provider.process(file_bytes, provider_config)
            tasks_db[task_id]["status"] = "completed"
            tasks_db[task_id]["result"] = result.to_dict()
            
    except Exception as e:
        logger.error(f"OCR Task Error: {str(e)}")
        tasks_db[task_id]["status"] = "failed"
        tasks_db[task_id]["error"] = str(e)


@app.post("/api/v1/ocr/upload", response_model=TaskResponse)
@limiter.limit("10/minute")  # Max 10 OCR uploads per minute
async def upload_file(
    request: Request,
    file: UploadFile = File(...), 
    background_tasks: BackgroundTasks = None,
    provider: Optional[str] = Query(None, description="Override active provider"),
    api_key: dict = Depends(verify_api_key)  # Protected!
):
    """
    Upload file for OCR processing (Requires API Key)
    
    Args:
        file: The file to process (JPEG, PNG, or PDF)
        provider: Optional provider override (uses active provider if not specified)
    """
    if file.content_type not in ["image/jpeg", "image/png", "application/pdf"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, and PDF are supported.")
    
    # Determine which provider to use (priority: query param > API key > global active)
    api_key_provider = api_key.get("provider", "")
    provider_name = provider or api_key_provider or get_active_provider()
    
    # Track usage - increment request count for this API key
    if api_key.get("id"):
        increment_usage(api_key["id"])
    
    # Validate provider exists
    if provider_name not in get_provider_names():
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider_name}")
    
    # Read file content
    content = await file.read()
    
    # Generate Task ID
    task_id = str(uuid.uuid4())
    
    # Init task status
    tasks_db[task_id] = {
        "status": "pending",
        "filename": file.filename,
        "provider": provider_name,
        "api_key_name": api_key.get("name", "unknown"),
        "custom_prompt": api_key.get("custom_prompt", "")
    }
    
    # Get custom prompt from API key
    custom_prompt = api_key.get("custom_prompt", "")
    
    # Trigger background processing with custom prompt
    background_tasks.add_task(process_ocr_task, task_id, content, provider_name, custom_prompt)
    
    logger.info(f"OCR task {task_id} created by API key: {api_key.get('name', 'unknown')} with custom_prompt: {bool(custom_prompt)}")
    
    return {"task_id": task_id, "status": "pending"}


@app.get("/api/v1/ocr/status/{task_id}")
def get_status(task_id: str, api_key: dict = Depends(verify_api_key)):
    """Check OCR task status (Requires API Key)"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks_db[task_id]
    return {
        "task_id": task_id, 
        "status": task["status"],
        "provider": task.get("provider", "unknown")
    }


@app.get("/api/v1/ocr/result/{task_id}")
def get_result(task_id: str, api_key: dict = Depends(verify_api_key)):
    """Get OCR result (Requires API Key)"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks_db[task_id]
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Task is not completed yet")
    
    return {
        "task_id": task_id,
        "status": "completed",
        "data": task.get("result")
    }


# ==========================================
# TOOLS API ENDPOINTS
# ==========================================

from fastapi.responses import StreamingResponse
import io

@app.post("/api/v1/tools/merge-pdf")
async def merge_pdf_endpoint(files: list[UploadFile] = File(...)):
    """Merge multiple PDF files into one"""
    
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="At least 2 PDF files are required")
    
    try:
        pdf_bytes_list = []
        for f in files:
            content = await f.read()
            pdf_bytes_list.append(content)
        
        result = merge_pdfs(pdf_bytes_list)
        
        return StreamingResponse(
            io.BytesIO(result),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=merged.pdf"}
        )
    except Exception as e:
        logger.error(f"Merge PDF error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/tools/split-pdf")
async def split_pdf_endpoint(
    file: UploadFile = File(...),
    mode: str = Query("all", description="Split mode: 'all' or 'range'"),
    range: Optional[str] = Query(None, description="Page range for mode='range'")
):
    """Split PDF into individual pages"""
    
    try:
        content = await file.read()
        result = split_pdf(content, mode=mode, page_range=range)
        
        if mode == "all":
            return StreamingResponse(
                io.BytesIO(result),
                media_type="application/zip",
                headers={"Content-Disposition": "attachment; filename=split-pages.zip"}
            )
        else:
            return StreamingResponse(
                io.BytesIO(result),
                media_type="application/pdf",
                headers={"Content-Disposition": "attachment; filename=extracted.pdf"}
            )
    except Exception as e:
        logger.error(f"Split PDF error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/tools/compress-pdf")
async def compress_pdf_endpoint(
    file: UploadFile = File(...),
    level: str = Query("medium", description="Compression level: low, medium, high")
):
    """Compress PDF file"""
    
    try:
        content = await file.read()
        result = compress_pdf(content, level=level)
        
        return StreamingResponse(
            io.BytesIO(result),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=compressed.pdf"}
        )
    except Exception as e:
        logger.error(f"Compress PDF error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/tools/image-converter")
async def image_converter_endpoint(
    file: UploadFile = File(...),
    format: str = Query("jpg", description="Target format: jpg, png, webp"),
    quality: int = Query(85, description="Quality for lossy formats (1-100)")
):
    """Convert image to different format"""
    
    try:
        content = await file.read()
        result = convert_image(content, target_format=format, quality=quality)
        
        mime_types = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp"
        }
        
        return StreamingResponse(
            io.BytesIO(result),
            media_type=mime_types.get(format, "image/jpeg"),
            headers={"Content-Disposition": f"attachment; filename=converted.{format}"}
        )
    except Exception as e:
        logger.error(f"Image convert error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class QRRequest(BaseModel):
    content: str
    size: int = 300

@app.post("/api/v1/tools/qr-generator")
async def qr_generator_endpoint(request: QRRequest):
    """Generate QR code"""
    
    try:
        result = generate_qr(request.content, size=request.size)
        
        return StreamingResponse(
            io.BytesIO(result),
            media_type="image/png",
            headers={"Content-Disposition": "attachment; filename=qrcode.png"}
        )
    except Exception as e:
        logger.error(f"QR generate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/tools/protect-pdf")
async def protect_pdf_endpoint(
    file: UploadFile = File(...),
    password: str = Form(...),
    api_key: APIKeyHeader = Depends(api_key_header)
):
    """
    Protect PDF with password
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
        
    try:
        content = await file.read()
        protected_pdf = protect_pdf(content, password)
        
        return StreamingResponse(
            io.BytesIO(protected_pdf), 
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="protected_{file.filename}"'}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error protecting PDF: {e}")
        raise HTTPException(status_code=500, detail="Failed to protect PDF")

@app.post("/api/v1/tools/unlock-pdf")
async def unlock_pdf_endpoint(
    file: UploadFile = File(...),
    password: str = Form(...),
    api_key: APIKeyHeader = Depends(api_key_header)
):
    """
    Unlock PDF with password (decrypt)
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
        
    try:
        content = await file.read()
        unlocked_pdf = unlock_pdf(content, password)
        
        return StreamingResponse(
            io.BytesIO(unlocked_pdf), 
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="unlocked_{file.filename}"'}
        )
    except ValueError as e:
        # Likely invalid password
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error unlocking PDF: {e}")
        raise HTTPException(status_code=500, detail="Failed to unlock PDF")


@app.post("/api/v1/tools/remove-bg")
async def remove_bg_endpoint(
    file: UploadFile = File(...),
    api_key: str = Header(None, alias="X-API-Key")
):
    """
    Remove background from image using AI (rembg)
    Returns PNG with transparent background
    """
    # Check file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File must be an image (JPEG, PNG, or WEBP)")
    
    try:
        content = await file.read()
        
        # Call the remove_background function
        result_bytes = remove_background(content)
        
        return StreamingResponse(
            io.BytesIO(result_bytes),
            media_type="image/png",
            headers={"Content-Disposition": f'attachment; filename="nobg_{file.filename}.png"'}
        )
    except ImportError as e:
        logger.error(f"AI tools not available: {e}")
        raise HTTPException(status_code=503, detail="AI background removal service is not available. Please check server logs.")
    except ValueError as e:
        logger.error(f"Remove background error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Remove background error: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove background from image")


@app.post("/api/v1/tools/pdf-to-word")
async def pdf_to_word_endpoint(
    file: UploadFile = File(...),
    api_key: str = Header(None, alias="X-API-Key")
):
    """
    Convert PDF to Word document (DOCX)
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        content = await file.read()
        result = pdf_to_word(content)
        
        # Get filename without extension
        original_name = file.filename or "document"
        if original_name.lower().endswith('.pdf'):
            original_name = original_name[:-4]
        
        return StreamingResponse(
            io.BytesIO(result),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{original_name}.docx"'}
        )
    except ValueError as e:
        logger.error(f"PDF to Word error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"PDF to Word error: {e}")
        raise HTTPException(status_code=500, detail="Failed to convert PDF to Word")


@app.post("/api/v1/tools/watermark-pdf")
async def watermark_pdf_endpoint(
    file: UploadFile = File(...),
    text: str = Form(..., description="Watermark text"),
    position: str = Form("diagonal", description="Position: diagonal or center"),
    opacity: float = Form(0.3, description="Opacity 0.0-1.0"),
    api_key: str = Header(None, alias="X-API-Key")
):
    """
    Add text watermark to PDF
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    if not text or len(text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Watermark text is required")
    
    # Validate opacity
    opacity = max(0.1, min(1.0, opacity))
    
    try:
        content = await file.read()
        result = add_watermark(content, text.strip(), position, opacity)
        
        return StreamingResponse(
            io.BytesIO(result),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="watermarked_{file.filename}"'}
        )
    except Exception as e:
        logger.error(f"Watermark PDF error: {e}")
        raise HTTPException(status_code=500, detail="Failed to add watermark to PDF")


@app.post("/api/v1/tools/word-to-pdf")
async def word_to_pdf_endpoint(
    file: UploadFile = File(...),
    api_key: str = Header(None, alias="X-API-Key")
):
    """
    Convert Word document (DOC/DOCX) to PDF using LibreOffice
    """
    # Check file type
    allowed_types = [
        "application/msword",  # .doc
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    ]
    
    # Also check by extension since some browsers may not set correct MIME type
    filename = file.filename or "document.docx"
    is_valid_ext = filename.lower().endswith(('.doc', '.docx'))
    
    if file.content_type not in allowed_types and not is_valid_ext:
        raise HTTPException(status_code=400, detail="File must be a Word document (DOC or DOCX)")
    
    try:
        content = await file.read()
        result = word_to_pdf(content, filename)
        
        # Get filename without extension
        original_name = filename
        if original_name.lower().endswith('.docx'):
            original_name = original_name[:-5]
        elif original_name.lower().endswith('.doc'):
            original_name = original_name[:-4]
        
        return StreamingResponse(
            io.BytesIO(result),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{original_name}.pdf"'}
        )
    except ValueError as e:
        logger.error(f"Word to PDF error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Word to PDF error: {e}")
        raise HTTPException(status_code=500, detail="Failed to convert Word to PDF")
