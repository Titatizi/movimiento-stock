# Procesador de Remitos - Agua Local

Herramienta AI para procesar imágenes de remitos y llenar automáticamente el formulario de movimientos de stock.

## Características

- **Procesamiento de imágenes con AI**: Soporta OpenAI, OpenRouter (con rotación de modelos gratuitos) y DeepSeek
- **Reglas de negocio automáticas**: Agrega items complementarios según las reglas configuradas
- **Automatización con Playwright**: Llena el formulario de Fillout automáticamente
- **Interfaz moderna**: Frontend en Next.js con drag & drop

## Reglas de Negocio Implementadas

1. **Equipo Lago/Rio** → Agrega "Cable Interlock 220V"
2. **Romi Plus** → Agrega "Conector Recto 8-6" + "Llave de paso 6-6"
3. **Tanque Hidroneumático** → Agrega "Bifurcación Y 6-6-6" + "Llave de paso 1/4-6"
4. **Tubo de CO2** → Agrega regulador (ZERICA para Lago, TALOS para Rio)
5. **Cualquier regulador** → Agrega "Conector 1/8-8"
6. **Equipo Lago** → Incluye "Bandeja de Goteo"
7. **120+ Botellas Cántaro 500** → Agrega 50% tapas plateadas + 50% negras

## Instalación

### Backend (Python)

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
playwright install chromium
```

### Frontend (Next.js)

```bash
cd frontend
npm install
```

## Configuración

Copia `.env.example` a `.env` y configura las claves API:

```env
LLM_PROVIDER=openrouter  # openai, openrouter, o deepseek
OPENROUTER_API_KEY=tu-clave-aqui
```

## Uso

### 1. Iniciar el backend

```bash
cd backend
.\venv\Scripts\activate
python main.py
```

El servidor se ejecutará en http://localhost:8000

### 2. Iniciar el frontend

```bash
cd frontend
npm run dev
```

El frontend estará en http://localhost:3000

### 3. Procesar un remito

1. Abre http://localhost:3000
2. Sube una imagen del remito (drag & drop o clic)
3. Revisa los items detectados y los agregados automáticamente
4. Haz clic en "Llenar Formulario"
5. El navegador se abrirá con el formulario llenado
6. Revisa y envía manualmente

## API Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/parse-image` | POST | Parsea imagen de remito |
| `/api/fill-form` | POST | Llena el formulario |
| `/api/submit-form` | POST | Envía el formulario |
| `/api/config` | GET | Configuración actual |

## Estructura del Proyecto

```
movimiento_stock/
├── backend/
│   ├── main.py          # FastAPI app
│   ├── llm_service.py   # Multi-provider LLM
│   ├── business_rules.py # Reglas automáticas
│   ├── form_filler.py   # Playwright automation
│   ├── models.py        # Pydantic schemas
│   └── config.py        # Configuración
├── frontend/
│   ├── app/
│   │   └── page.tsx     # Página principal
│   └── components/
│       ├── ImageUpload.tsx
│       ├── ItemsList.tsx
│       └── StatusDisplay.tsx
└── .env.example
```

## Desarrollo

El proyecto usa:
- **Backend**: Python 3.11+, FastAPI, Playwright, OpenAI SDK
- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS
