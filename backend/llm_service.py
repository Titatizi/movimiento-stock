"""
Multi-provider LLM service for parsing delivery note images.
Supports OpenAI, OpenRouter (with model rotation), and DeepSeek.
"""
import base64
import json
import random
import httpx
from openai import OpenAI
from typing import Optional
from models import DeliveryNoteItem, ParsedDeliveryNote
from config import (
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OPENROUTER_API_KEY,
    DEEPSEEK_API_KEY,
    OPENROUTER_MODELS,
)


SYSTEM_PROMPT = """You are an expert at reading handwritten delivery notes (remitos) in Spanish.
Your task is to extract the list of products and their quantities from the image.

VALID PRODUCT NAMES (use these exact names):
- EQUIPO LAGO
- EQUIPO RIO  
- ROMI PLUS
- TANQUE HIDRONEUMATICO
- TUBO DE CO2 (2.5KG)
- TUBO DE CO2 (3KG)
- TUBO DE CO2 (5KG)
- TUBO DE CO2 (8KG)
- TUBO DE CO2 (10KG)
- MANOMETRO
- CABLE INTERLOCK 220V
- PROTECTOR DE TENSION
- BANDEJA DE GOTEO
- BOTELLAS CANTARO 500
- BOTELLAS CANTARO 750
- TAPAS CANTARO PLATEADAS
- TAPAS CANTARO NEGRAS
- CEPILLO DE LIMPIEZA
- LLAVE DE PASO
- CONECTOR
- FUENTE

SPECIAL RULES FOR PARSING:
1. When you see "EQUIPO LAGO + CABLE" or similar, split into TWO separate items:
   - "EQUIPO LAGO" (quantity 1)
   - "CABLE INTERLOCK 220V" (quantity 1)

2. When you see "ROMI PLUS + FUENTE", record ONLY "ROMI PLUS" - the FUENTE is included with it.

3. When you see "BOTELLAS CANTARO 500 + TAPAS", record ONLY the bottles without "+ TAPAS":
   - "BOTELLAS CANTARO 500" (with the quantity)
   The caps will be added automatically by the system.

4. Common handwriting errors to correct:
   - "HIDRONEUMATILO" → "HIDRONEUMATICO"
   - "PROTEITOR" → "PROTECTOR"
   - "SKG" → "5KG" (for CO2 tubes)
   - "TENSIÓN" → "TENSION"

5. The quantity column is on the left side labeled "CANT."

Return your response as a JSON object:
{
  "items": [
    {"product": "EQUIPO LAGO", "quantity": 1},
    {"product": "CABLE INTERLOCK 220V", "quantity": 1}
  ],
  "client_name": "client name from Señores field if visible",
  "remito_number": "remito number if visible",
  "fecha": "date if visible in DD/MM/YY format"
}

IMPORTANT: Use the EXACT product names from the valid list above. Correct any typos."""


class LLMService:
    """Multi-provider LLM service with fallback support."""
    
    def __init__(self):
        self.provider = LLM_PROVIDER
        self._openrouter_model_index = 0
        self._failed_models = set()
    
    def _encode_image(self, image_data: bytes) -> str:
        """Encode image to base64."""
        return base64.b64encode(image_data).decode("utf-8")
    
    def _get_next_openrouter_model(self) -> Optional[str]:
        """Get next available OpenRouter model for rotation."""
        available = [m for m in OPENROUTER_MODELS if m not in self._failed_models]
        if not available:
            # Reset and try again
            self._failed_models.clear()
            available = OPENROUTER_MODELS
        
        # Random selection for better distribution
        return random.choice(available)
    
    async def _call_openai(self, image_base64: str) -> dict:
        """Call OpenAI API with vision."""
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please extract the products and quantities from this delivery note image."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _call_openrouter(self, image_base64: str, model: str) -> dict:
        """Call OpenRouter API with vision."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/delivery-note-processor",
                    "X-Title": "Delivery Note Processor"
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Please extract the products and quantities from this delivery note image. Return JSON only."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 2000
                },
                timeout=60.0
            )
            
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Parse JSON from response (may be wrapped in markdown)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content.strip())
    
    async def _call_deepseek(self, image_base64: str) -> dict:
        """Call DeepSeek API with vision."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-vision",
                    "messages": [
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Please extract the products and quantities from this delivery note image."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 2000
                },
                timeout=60.0
            )
            
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Parse JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            
            return json.loads(content.strip())
    
    async def parse_image(self, image_data: bytes) -> ParsedDeliveryNote:
        """Parse a delivery note image using the configured LLM provider."""
        image_base64 = self._encode_image(image_data)
        
        if self.provider == "openai":
            result = await self._call_openai(image_base64)
        elif self.provider == "openrouter":
            # Try models with fallback
            last_error = None
            for _ in range(len(OPENROUTER_MODELS)):
                model = self._get_next_openrouter_model()
                try:
                    result = await self._call_openrouter(image_base64, model)
                    break
                except Exception as e:
                    self._failed_models.add(model)
                    last_error = e
                    continue
            else:
                raise Exception(f"All OpenRouter models failed. Last error: {last_error}")
        elif self.provider == "deepseek":
            result = await self._call_deepseek(image_base64)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")
        
        # Convert to ParsedDeliveryNote
        items = [
            DeliveryNoteItem(
                product=item["product"],
                quantity=item.get("quantity", 1)
            )
            for item in result.get("items", [])
        ]
        
        return ParsedDeliveryNote(
            items=items,
            client_name=result.get("client_name"),
            remito_number=result.get("remito_number"),
            fecha=result.get("fecha")
        )


# Singleton instance
llm_service = LLMService()
