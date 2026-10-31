# Skill: FastAPI Patterns 2025
triggers: [fastapi, sqlalchemy, pydantic, python backend, endpoint, router]

## Dependency Injection Correcta

```python
# CORRECTO — async session via Depends
@router.get("/items/{id}", response_model=ItemRead)
async def get_item(id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = await db.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return item

# MAL — session manual dentro del endpoint
async def get_item(id: int):
    async with AsyncSessionLocal() as db:  # NO — rompe el ciclo de vida
        ...
```

## Pydantic v2 — Patrones Obligatorios

```python
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Nombre del item")
    price: float = Field(..., gt=0, description="Precio debe ser positivo")
    email: EmailStr  # validación automática de formato email

class ItemRead(BaseModel):
    id: int
    name: str
    price: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)  # permite .model_validate(orm_obj)
```

## Manejo de Errores Estándar

```python
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

# Códigos correctos
raise HTTPException(status_code=400, detail="Solicitud inválida")
raise HTTPException(status_code=401, detail="No autenticado")
raise HTTPException(status_code=403, detail="Sin permisos suficientes")
raise HTTPException(status_code=404, detail="Recurso no encontrado")
raise HTTPException(status_code=409, detail="Recurso ya existe")
raise HTTPException(status_code=422, detail="Datos de entrada inválidos")

# Handler global para errores no esperados (NUNCA exponer stack trace)
@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})
```

## Queries Async Correctas (SQLAlchemy 2.x)

```python
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

# Buscar uno
result = await db.execute(select(User).where(User.email == email))
user = result.scalar_one_or_none()

# Buscar muchos con paginación
result = await db.execute(select(Item).offset(skip).limit(limit).order_by(Item.created_at.desc()))
items = result.scalars().all()

# Crear
db.add(new_item)
await db.commit()
await db.refresh(new_item)  # para obtener id y timestamps generados

# Actualizar
await db.execute(update(Item).where(Item.id == id).values(name=new_name))
await db.commit()
```

## CORS Seguro

```python
# NUNCA en producción:
allow_origins=["*"]

# Correcto — lista explícita desde env
import os
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_credentials=True, ...)
```

## Rate Limiting con slowapi

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/login")
@limiter.limit("5/minute")  # máx 5 intentos por minuto por IP
async def login(request: Request, ...):
    ...
```
