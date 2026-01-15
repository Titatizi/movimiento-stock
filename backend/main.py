"""
FastAPI backend for the Delivery Note Processor.
"""
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from models import (
    ParsedDeliveryNote,
    ParseImageResponse,
    FormFillRequest,
    FormFillResponse,
    DeliveryNoteItem
)
from llm_service import llm_service
from business_rules import apply_business_rules, map_to_form_value
from form_filler import form_filler
from config import DEFAULT_SALIDA, DEFAULT_ENTRADA


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    yield
    # Cleanup
    await form_filler._close_browser()


app = FastAPI(
    title="Delivery Note Processor",
    description="AI-powered tool to parse delivery notes and fill stock movement forms",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Delivery Note Processor API"}


@app.post("/api/parse-image", response_model=ParseImageResponse)
async def parse_image(file: UploadFile = File(...)):
    """
    Parse a delivery note image and extract products.
    
    Uploads an image file, sends it to an LLM for parsing,
    and applies business rules to add automatic items.
    """
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await file.read()
        
        # Parse with LLM
        parsed_note = await llm_service.parse_image(image_data)
        
        # Map products to form values
        for item in parsed_note.items:
            if not item.form_value:
                item.form_value = map_to_form_value(item.product)
        
        # Apply business rules
        enhanced_note = apply_business_rules(parsed_note)
        
        return ParseImageResponse(
            success=True,
            parsed_note=enhanced_note
        )
        
    except Exception as e:
        return ParseImageResponse(
            success=False,
            error=str(e)
        )


@app.post("/api/fill-form", response_model=FormFillResponse)
async def fill_form(request: FormFillRequest):
    """
    Fill the Fillout form with the provided items.
    
    Uses Playwright to automate form filling.
    Does not auto-submit - user must review and submit manually.
    """
    try:
        result = await form_filler.fill_form(
            items=request.items,
            fecha=request.fecha,
            salida=request.salida,
            entrada=request.entrada,
            comentarios=request.comentarios
        )
        return result
        
    except Exception as e:
        return FormFillResponse(
            success=False,
            message=f"Error: {str(e)}",
            items_filled=0
        )


@app.post("/api/submit-form", response_model=FormFillResponse)
async def submit_form():
    """
    Submit the currently filled form.
    
    Call this after reviewing the form in the browser.
    """
    try:
        result = await form_filler.submit_form()
        return result
    except Exception as e:
        return FormFillResponse(
            success=False,
            message=f"Error: {str(e)}",
            items_filled=0
        )


@app.get("/api/config")
async def get_config():
    """Get current configuration (non-sensitive)."""
    from config import LLM_PROVIDER, OPENROUTER_MODELS
    return {
        "llm_provider": LLM_PROVIDER,
        "default_salida": DEFAULT_SALIDA,
        "default_entrada": DEFAULT_ENTRADA,
        "openrouter_models": OPENROUTER_MODELS
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
