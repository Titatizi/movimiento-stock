"""
Playwright-based form filler for the Fillout stock movement form.
"""
import asyncio
from datetime import date
from playwright.async_api import async_playwright, Page, Browser
from typing import Optional
from models import DeliveryNoteItem, FormFillResponse
from config import FORM_URL, DEFAULT_SALIDA, DEFAULT_ENTRADA


class FormFiller:
    """Fills the Fillout form using Playwright."""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._playwright = None
    
    async def _init_browser(self):
        """Initialize a fresh browser for each request."""
        # Always create a fresh browser to avoid stale connections
        if self.browser:
            try:
                await self.browser.close()
            except:
                pass
        
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
    
    async def _close_browser(self):
        """Close browser safely."""
        try:
            if self.browser:
                await self.browser.close()
        except:
            pass
        self.browser = None
        self.page = None
    
    async def _wait_for_form_load(self):
        """Wait for the form to fully load."""
        await self.page.wait_for_selector('[aria-label="Fecha del movimiento"]', timeout=30000)
        await asyncio.sleep(1)  # Extra wait for dynamic content
    
    async def _fill_date(self, fecha: Optional[str] = None):
        """Fill the date field."""
        if fecha is None:
            fecha = date.today().strftime("%m/%d/%Y")
        else:
            # Convert DD/MM/YY to MM/DD/YYYY
            parts = fecha.split("/")
            if len(parts) == 3:
                day, month, year = parts
                if len(year) == 2:
                    year = "20" + year
                fecha = f"{month}/{day}/{year}"
        
        # Use specific aria-label to target the correct date input
        date_input = self.page.locator('[aria-label="Fecha del movimiento"]')
        await date_input.click()
        await date_input.fill(fecha)
        await self.page.keyboard.press("Escape")
    
    async def _fill_dropdown(self, aria_label: str, value: str):
        """Fill a react-select dropdown using aria-label."""
        # React-select dropdowns have an input with aria-label
        dropdown_input = self.page.locator(f'[aria-label="{aria_label}"]')
        
        # Click to focus and open
        await dropdown_input.click()
        await asyncio.sleep(0.3)
        
        # Type to search (use first part of value for better matching)
        search_text = value.split("|")[0].strip() if "|" in value else value[:25]
        await dropdown_input.fill(search_text)
        await asyncio.sleep(0.5)
        
        # Click the matching option (react-select options have role="option")
        option = self.page.locator(f'[role="option"]:has-text("{search_text}")').first
        if await option.count() > 0:
            await option.click()
        else:
            # Try pressing Enter to select first result
            await self.page.keyboard.press("Enter")
        
        await asyncio.sleep(0.2)
    
    async def _fill_text_input(self, aria_label: str, value: str):
        """Fill a text input using aria-label."""
        input_field = self.page.locator(f'[aria-label="{aria_label}"]')
        await input_field.fill(value)
    
    async def _fill_number_input(self, aria_label: str, value: int):
        """Fill a number input using aria-label."""
        input_field = self.page.locator(f'[aria-label="{aria_label}"]')
        await input_field.fill(str(value))
    
    async def _set_item_count(self, count: int):
        """Set the number of items to show product fields."""
        input_field = self.page.locator('[aria-label="Cantidad de items (max. 30)"]')
        await input_field.fill(str(count))
        await asyncio.sleep(1.5)  # Wait for fields to appear
    
    async def fill_form(
        self,
        items: list[DeliveryNoteItem],
        fecha: Optional[str] = None,
        salida: str = DEFAULT_SALIDA,
        entrada: str = DEFAULT_ENTRADA,
        comentarios: Optional[str] = None
    ) -> FormFillResponse:
        """Fill the complete form with the given items."""
        try:
            await self._init_browser()
            
            # Navigate to form
            await self.page.goto(FORM_URL)
            await self._wait_for_form_load()
            
            # Fill basic fields
            await self._fill_date(fecha)
            await asyncio.sleep(0.3)
            
            # Fill SALIDA dropdown
            await self._fill_dropdown("SALIDA", salida)
            await asyncio.sleep(0.3)
            
            # Fill ENTRADA dropdown
            await self._fill_dropdown("ENTRADA", entrada)
            await asyncio.sleep(0.3)
            
            # Fill Comentarios
            if comentarios:
                await self._fill_text_input("Comentarios", comentarios)
            else:
                await self._fill_text_input("Comentarios", "Generado automáticamente desde remito")
            
            # Set item count to show all product fields
            await self._set_item_count(len(items))
            
            # Fill each product and quantity
            for i, item in enumerate(items, start=1):
                product_label = f"{i:02d}.Producto"
                quantity_label = f"{i:02d}.Cantidad"
                
                # Scroll into view if needed
                await self.page.locator(f'[aria-label="{product_label}"]').scroll_into_view_if_needed()
                await asyncio.sleep(0.2)
                
                # Fill product dropdown
                form_value = item.form_value or item.product
                await self._fill_dropdown(product_label, form_value)
                await asyncio.sleep(0.2)
                
                # Fill quantity
                await self._fill_number_input(quantity_label, item.quantity)
                await asyncio.sleep(0.1)
            
            # Take screenshot before submit
            screenshot_path = "form_filled_screenshot.png"
            await self.page.screenshot(path=screenshot_path)
            
            # Auto-submit the form
            submit_button = self.page.locator('button:has-text("Submit")').first
            await submit_button.scroll_into_view_if_needed()
            await asyncio.sleep(0.3)
            await submit_button.click()
            await asyncio.sleep(3)  # Wait for submission
            
            # Check for success
            success_text = self.page.locator('text="Thank you"')
            if await success_text.count() > 0:
                return FormFillResponse(
                    success=True,
                    message="Formulario enviado exitosamente!",
                    items_filled=len(items),
                    screenshot_path=screenshot_path
                )
            else:
                return FormFillResponse(
                    success=True,
                    message="Formulario llenado y enviado. Verifique en Fillout.",
                    items_filled=len(items),
                    screenshot_path=screenshot_path
                )
            
        except Exception as e:
            return FormFillResponse(
                success=False,
                message=f"Error filling form: {str(e)}",
                items_filled=0
            )
        finally:
            # Close browser after submission
            await self._close_browser()
    
    async def submit_form(self):
        """Submit the form after user review."""
        if self.page:
            submit_button = self.page.locator('button:has-text("Submit")').first
            await submit_button.click()
            await asyncio.sleep(2)
            
            # Check for success
            success_text = self.page.locator('text="Thank you"')
            if await success_text.count() > 0:
                return FormFillResponse(
                    success=True,
                    message="Form submitted successfully!",
                    items_filled=0
                )
            else:
                return FormFillResponse(
                    success=False,
                    message="Form submission may have failed. Please check.",
                    items_filled=0
                )


# Singleton instance
form_filler = FormFiller()
