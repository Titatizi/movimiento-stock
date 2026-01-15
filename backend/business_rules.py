"""
Business rules engine for automatic item additions.

Rules:
1. Equipo Lago/Rio → Add Cable Interlock 220V (only if not already in list)
2. Romi Plus → Add Conector Recto 8-6 + Llave de paso 6-6
3. Tanque Hidroneumático → Add Bifurcación Y 6-6-6 + Llave de paso 1/4-6
4. Tubo CO2 → Add Regulador (ZERICA for Lago, TALOS for Rio)
5. Any regulator → Add Conector 1/8-8
6. Equipo Lago → Bandeja de Goteo is INCLUDED (no need to add if already parsed from note)
7. Botellas Cántaro 500 (any qty) → Add 50% Tapas Plateadas + 50% Tapas Negras
"""
from models import DeliveryNoteItem, ParsedDeliveryNote
from config import PRODUCT_MAPPING


def normalize_product_name(name: str) -> str:
    """Normalize product name for matching."""
    return name.lower().strip()


def map_to_form_value(product_name: str) -> str:
    """Map a product name to its form dropdown value."""
    normalized = normalize_product_name(product_name)
    
    # Direct mapping
    for key, value in PRODUCT_MAPPING.items():
        if key in normalized:
            return value
    
    # Return original if no mapping found
    return product_name


def apply_business_rules(parsed_note: ParsedDeliveryNote) -> ParsedDeliveryNote:
    """Apply all business rules to add required items."""
    items = list(parsed_note.items)
    new_items = []
    
    has_equipo_lago = False
    has_equipo_rio = False
    has_romi_plus = False
    has_tanque_hidro = False
    has_tubo_co2 = False
    has_regulator = False
    cantaro_500_qty = 0
    
    # First pass: detect what's in the order and map form values
    for item in items:
        normalized = normalize_product_name(item.product)
        item.form_value = map_to_form_value(item.product)
        
        if "equipo lago" in normalized or "lago" in normalized:
            has_equipo_lago = True
        if "equipo rio" in normalized or "rio" in normalized and "purificador" not in normalized:
            has_equipo_rio = True
        if "romi plus" in normalized or "romi" in normalized:
            has_romi_plus = True
        if "tanque" in normalized and ("hidro" in normalized or "hidroneumático" in normalized or "hidroneumatico" in normalized):
            has_tanque_hidro = True
        if "tubo" in normalized and "co2" in normalized:
            has_tubo_co2 = True
        if "regulador" in normalized or "manómetro" in normalized or "manometro" in normalized:
            has_regulator = True
        if "botellas" in normalized and "cantaro" in normalized and "500" in normalized:
            cantaro_500_qty = item.quantity
    
    # Rule 1: Equipo Lago/Rio → Cable Interlock 220V
    if has_equipo_lago or has_equipo_rio:
        if not any("cable interlock" in normalize_product_name(i.product) for i in items):
            new_items.append(DeliveryNoteItem(
                product="Cable Interlock 220V",
                quantity=1,
                form_value="INSUMO | cooler | Cable interlock 220 volt",
                is_auto_added=True
            ))
    
    # Rule 2: Romi Plus → Conector Recto 8-6 + Llave de paso 6-6
    if has_romi_plus:
        if not any("conector" in normalize_product_name(i.product) and "8-6" in i.product for i in items):
            new_items.append(DeliveryNoteItem(
                product="Conector Recto 8-6",
                quantity=1,
                form_value="CONECTOR | acople rapido | 8-6",
                is_auto_added=True
            ))
        if not any("llave" in normalize_product_name(i.product) and "6-6" in i.product for i in items):
            new_items.append(DeliveryNoteItem(
                product="Llave de paso 6-6",
                quantity=1,
                form_value="CONECTOR | llave de paso | 6-6",
                is_auto_added=True
            ))
    
    # Rule 3: Tanque Hidroneumático → Bifurcación Y 6-6-6 + Llave de paso 1/4-6
    if has_tanque_hidro:
        if not any("bifurcacion" in normalize_product_name(i.product) or "bifurcación" in normalize_product_name(i.product) for i in items):
            new_items.append(DeliveryNoteItem(
                product="Bifurcación Y 6-6-6",
                quantity=1,
                form_value="CONECTOR | acople rapido - bifurcacion Y | 6-6-6",
                is_auto_added=True
            ))
        if not any("llave" in normalize_product_name(i.product) and "1/4" in i.product for i in items):
            new_items.append(DeliveryNoteItem(
                product="Llave de paso 1/4-6",
                quantity=1,
                form_value="CONECTOR | llave de paso | 1/4-6",
                is_auto_added=True
            ))
    
    # Rule 4: Tubo CO2 → Add Regulador (needs to check if regulator already present)
    if has_tubo_co2 and not has_regulator:
        # Determine regulator type based on equipment
        if has_equipo_lago:
            regulator_value = "CO2 | regulador | Zerica"
            regulator_name = "Regulador ZERICA"
        elif has_equipo_rio:
            regulator_value = "CO2 | regulador | Talos"
            regulator_name = "Regulador TALOS"
        else:
            # Default to ZERICA if no equipment specified
            regulator_value = "CO2 | regulador | Zerica"
            regulator_name = "Regulador/Manómetro"
        
        new_items.append(DeliveryNoteItem(
            product=regulator_name,
            quantity=1,
            form_value=regulator_value,
            is_auto_added=True
        ))
        has_regulator = True
    
    # Rule 5: Any regulator → Add Conector 1/8-8
    if has_regulator:
        if not any("1/8" in i.product for i in items) and not any("1/8" in i.product for i in new_items):
            new_items.append(DeliveryNoteItem(
                product="Conector 1/8-8",
                quantity=1,
                form_value="CONECTOR | acople rapido | Rosca macho 1/8 - 8",
                is_auto_added=True
            ))
    
    # Rule 6: Equipo Lago → Bandeja de Goteo is INCLUDED
    # If the note says "Bandeja de Goteo" separately, keep it.
    # If Equipo Lago is present but no Bandeja, add it (it's included with the equipment)
    if has_equipo_lago:
        if not any("bandeja" in normalize_product_name(i.product) for i in items):
            new_items.append(DeliveryNoteItem(
                product="Bandeja de Goteo (incluida con Lago)",
                quantity=1,
                form_value="EQUIPO | cooler | Bandeja metalica LAGO",
                is_auto_added=True
            ))
    
    # Rule 7: Botellas Cántaro 500 → 50% Tapas Plateadas + 50% Tapas Negras
    # Applies to ANY quantity of bottles
    if cantaro_500_qty > 0:
        half_qty = cantaro_500_qty // 2
        other_half = cantaro_500_qty - half_qty  # Handle odd numbers
        # Check if caps already exist
        has_plateadas = any("plateada" in normalize_product_name(i.product) for i in items)
        has_negras = any("negra" in normalize_product_name(i.product) for i in items)
        
        if not has_plateadas:
            new_items.append(DeliveryNoteItem(
                product=f"Tapas Cántaro Plateadas",
                quantity=half_qty,
                form_value="ENVASADO | tapas | Tapas Cantaro Plateadas",
                is_auto_added=True
            ))
        if not has_negras:
            new_items.append(DeliveryNoteItem(
                product=f"Tapas Cántaro Negras",
                quantity=other_half,
                form_value="ENVASADO | tapas | Tapas Cantaro Negras",
                is_auto_added=True
            ))
    
    # Combine original items with auto-added items
    all_items = items + new_items
    
    return ParsedDeliveryNote(
        items=all_items,
        raw_text=parsed_note.raw_text,
        client_name=parsed_note.client_name,
        remito_number=parsed_note.remito_number,
        fecha=parsed_note.fecha
    )
