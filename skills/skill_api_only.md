# Skill: API REST pura (FastAPI sin frontend)

## Stack
- **Framework:** FastAPI 0.115+ con lifespan events
- **ORM:** SQLAlchemy 2.x async + asyncpg
- **Validación:** Pydantic v2 con ConfigDict
- **Auth:** API keys en header o JWT en Authorization Bearer
- **Rate limiting:** slowapi
- **Docs:** OpenAPI automático en /docs

## Estructura
```
app/
├── main.py              # FastAPI app + lifespan
├── routers/
│   ├── users.py
│   └── items.py
├── models/              # SQLAlchemy ORM
├── schemas/             # Pydantic request/response
├── services/            # Lógica de negocio
├── dependencies.py      # get_db, get_current_user
└── config.py
```

## Setup con lifespan
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()          # Startup
    yield
    await engine.dispose()   # Shutdown

app = FastAPI(lifespan=lifespan)
```

## Modelo + Schema patrón
```python
# models/user.py
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

# schemas/user.py
class UserCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    email: EmailStr

class UserOut(UserCreate):
    id: int
    created_at: datetime
```

## Auth con API key
```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_key(key: str = Depends(api_key_header)):
    if key != settings.API_KEY:
        raise HTTPException(403, "Invalid API key")
    return key
```

## Rate limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/items")
@limiter.limit("30/minute")
async def list_items(request: Request, db: AsyncSession = Depends(get_db)):
    ...
```

## Paginación cursor-based
```python
@app.get("/items")
async def list_items(cursor: int = 0, limit: int = 20):
    result = await db.execute(
        select(Item).where(Item.id > cursor).limit(limit).order_by(Item.id)
    )
    items = result.scalars().all()
    next_cursor = items[-1].id if len(items) == limit else None
    return {"items": items, "next_cursor": next_cursor}
```

## Sin frontend
- No servir archivos estáticos
- CORS solo para orígenes específicos desde env
- Respuestas siempre JSON con estructura consistente: `{data, error, meta}`
