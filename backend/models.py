"""
Pydantic models for the Delivery Note Processor API.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import date


class DeliveryNoteItem(BaseModel):
    """A single item from a delivery note."""
    product: str
    quantity: int
    form_value: Optional[str] = None  # Mapped form value
    is_auto_added: bool = False  # True if added by business rules


class ParsedDeliveryNote(BaseModel):
    """Parsed delivery note with all items."""
    items: list[DeliveryNoteItem]
    raw_text: Optional[str] = None
    client_name: Optional[str] = None
    remito_number: Optional[str] = None
    fecha: Optional[str] = None


class FormFillRequest(BaseModel):
    """Request to fill the form with parsed items."""
    items: list[DeliveryNoteItem]
    fecha: Optional[str] = None  # If None, uses today
    salida: str = "Superi"
    entrada: str = "Instalación Cliente"
    comentarios: Optional[str] = None


class FormFillResponse(BaseModel):
    """Response after form filling attempt."""
    success: bool
    message: str
    items_filled: int
    screenshot_path: Optional[str] = None


class ParseImageResponse(BaseModel):
    """Response from image parsing."""
    success: bool
    parsed_note: Optional[ParsedDeliveryNote] = None
    error: Optional[str] = None
