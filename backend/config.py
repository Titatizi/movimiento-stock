"""
Configuration management for the Delivery Note Processor.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# LLM Provider settings
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")  # openai, openrouter, deepseek
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# Default form values
DEFAULT_SALIDA = os.getenv("DEFAULT_SALIDA", "Superi")
DEFAULT_ENTRADA = os.getenv("DEFAULT_ENTRADA", "Instalación Cliente")

# OpenRouter free vision models for rotation
OPENROUTER_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-exp-1206:free",
    "meta-llama/llama-3.2-90b-vision-instruct:free",
    "meta-llama/llama-3.2-11b-vision-instruct:free",
    "qwen/qwen-2-vl-7b-instruct:free",
]

# Form URL
FORM_URL = "https://forms.fillout.com/t/jkCP1KMMq8us"

# Product mapping from handwritten terms to form values
PRODUCT_MAPPING = {
    # Equipment
    "equipo lago": "EQUIPO | cooler | LAGO",
    "equipo rio": "EQUIPO | cooler | RIO",
    "romi plus": "EQUIPO | purificador | Romi Plus",
    "tanque hidroneumatico": "EQUIPO | tanque | Tanque Hidro. 4G",
    "tanque hidroneumático": "EQUIPO | tanque | Tanque Hidro. 4G",
    
    # CO2
    "tubo de co2 2.5": "CO2 | tubo | Tubo de co2 de 2,5 Kg",
    "tubo de co2 2,5": "CO2 | tubo | Tubo de co2 de 2,5 Kg",
    "tubo de co2 3": "CO2 | tubo | Tubo de co2 de 3 Kg",
    "tubo de co2 5": "CO2 | tubo | Tubo de co2 de 5 Kg",
    "tubo de co2 5kg": "CO2 | tubo | Tubo de co2 de 5 Kg",
    "tubos de co2 5kg": "CO2 | tubo | Tubo de co2 de 5 Kg",
    "tubo de co2 8": "CO2 | tubo | Tubo de co2 de 8 Kg",
    "tubo de co2 10": "CO2 | tubo | Tubo de co2 de 10 Kg",
    "regulador zerica": "CO2 | regulador | Zerica",
    "regulador talos": "CO2 | regulador | Talos",
    "manometro": "CO2 | regulador | Zerica",  # Default, will be adjusted by rules
    "manómetro": "CO2 | regulador | Zerica",
    
    # Connectors
    "conector recto 8-6": "CONECTOR | acople rapido | 8-6",
    "conector 1/8-8": "CONECTOR | acople rapido | Rosca macho 1/8 - 8",
    "llave de paso 6-6": "CONECTOR | llave de paso | 6-6",
    "llave de paso 1/4-6": "CONECTOR | llave de paso | 1/4-6",
    "bifurcacion y 6-6-6": "CONECTOR | acople rapido - bifurcacion Y | 6-6-6",
    "bifurcación y 6-6-6": "CONECTOR | acople rapido - bifurcacion Y | 6-6-6",
    "llave de ai": "CONECTOR | llave de paso | 6-6",  # Assuming this is llave de agua
    
    # Bottles and caps
    "botellas cantaro 500": "ENVASADO | botellas | Cantaro 500",
    "botellas cántaro 500": "ENVASADO | botellas | Cantaro 500",
    "tapas cantaro plateadas": "ENVASADO | tapas | Tapas Cantaro Plateadas",
    "tapas cántaro plateadas": "ENVASADO | tapas | Tapas Cantaro Plateadas",
    "tapas cantaro negras": "ENVASADO | tapas | Tapas Cantaro Negras",
    "tapas cántaro negras": "ENVASADO | tapas | Tapas Cantaro Negras",
    
    # Accessories
    "bandeja de goteo": "EQUIPO | cooler | Bandeja metalica LAGO",
    "cable interlock": "INSUMO | cooler | Cable interlock 220 volt",
    "cable interlock 220v": "INSUMO | cooler | Cable interlock 220 volt",
    "protector de tension": "INSUMO | cooler | Protector de tension",
    "protector de tensión": "INSUMO | cooler | Protector de tension",
    "cepillo de limpieza": "REPUESTOS | limpieza | Cepillos botellas",
    "cepillo limpieza": "REPUESTOS | limpieza | Cepillos botellas",
    
    # Purifier accessories
    "fuente": "REPUESTOS | purificador | Fuente de 220 a 24 volt",
}
