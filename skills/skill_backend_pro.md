# Skill: Backend Pro — FastAPI + PostgreSQL + Next.js 2025
triggers: [fastapi, backend, api rest, sqlalchemy, postgresql, base de datos, full-stack, fullstack, endpoint, router, auth, jwt]

## Stack Canónico 2025

| Capa | Tecnología | Notas |
|:---|:---|:---|
| Backend Framework | FastAPI 0.115+ | lifespan events, no @on_event |
| ORM | SQLAlchemy 2.x async | AsyncSession, async_sessionmaker |
| Migraciones | Alembic (async) | NUNCA create_all() en prod |
| Auth | PyJWT + passlib[bcrypt] | tokens en httpOnly cookies |
| Base de Datos | PostgreSQL 16+ | Supabase (cloud) / Docker (local) |
| Validación | Pydantic v2 | ConfigDict(from_attributes=True) |
| Frontend | Next.js 15 + React 19 + Tailwind v4 | App Router, Server Components |
| HTTP Client | TanStack Query v5 + fetch nativo | NO axios salvo legacy |
| Rate Limiting | slowapi | endpoints públicos y auth |
| Logging | structlog | NUNCA print() en producción |

## Estructura de Archivos Backend

```
backend/
├── main.py              ← FastAPI app con lifespan, CORS, routers
├── database.py          ← AsyncEngine, async_sessionmaker, get_db
├── models/
│   └── user.py          ← SQLAlchemy ORM models (Base, tablas)
├── schemas/
│   └── user.py          ← Pydantic v2 schemas (Input/Output separados)
├── routers/
│   ├── auth.py          ← POST /api/auth/login, /register, /refresh, /logout
│   └── [resource].py   ← CRUD del recurso principal
├── services/
│   └── auth_service.py  ← lógica de negocio (hash, token, verify)
├── middleware/
│   └── rate_limit.py    ← slowapi limiter
├── core/
│   └── config.py        ← settings via pydantic-settings
├── alembic/             ← migraciones
└── requirements.txt
```

## main.py — Plantilla con Lifespan

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from .routers import auth, users
from .core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown
    await engine.dispose()

app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # NUNCA ["*"] en producción
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])

@app.get("/health")
async def health():
    return {"status": "ok"}
```

## Auth — httpOnly Cookies (NO localStorage)

```python
# routers/auth.py
from fastapi import APIRouter, Response, Depends, HTTPException
from ..services.auth_service import create_tokens, verify_password, get_user_by_email

router = APIRouter()

@router.post("/login")
async def login(credentials: LoginSchema, response: Response, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    access_token, refresh_token = create_tokens(user.id)

    # Tokens en httpOnly cookies — inaccesibles desde JavaScript
    response.set_cookie("access_token", access_token, httponly=True, secure=True, samesite="lax", max_age=1800)
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=True, samesite="lax", max_age=604800)
    return {"user": {"id": user.id, "email": user.email, "name": user.name}}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"ok": True}
```

## Pydantic v2 — Schemas

```python
from pydantic import BaseModel, EmailStr, ConfigDict

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str  # solo para input, nunca en output

class UserRead(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)  # permite crear desde ORM model
```

## SQLAlchemy 2.x Async

```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from .core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

## Reglas de Oro Anti-Error

1. NUNCA mezcles SQLAlchemy model con Pydantic schema. Son capas distintas.
2. SIEMPRE response_model= en endpoints FastAPI para serializar correctamente.
3. NUNCA crees AsyncSession manualmente — usa Depends(get_db).
4. Auth en httpOnly cookies. NUNCA retornes el token JWT en el body para que el frontend lo guarde.
5. Passwords: passlib hash siempre. NUNCA texto plano, MD5, SHA1.
6. SQL: SIEMPRE parámetros bindados. NUNCA f-strings en queries.
7. Rate limiting en /login y /register con slowapi.
8. lifespan en lugar de @app.on_event (deprecado desde FastAPI 0.95).

## docker-compose.yml para Desarrollo Local

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${DB_USER:-dev}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-devpassword}
      POSTGRES_DB: ${DB_NAME:-appdb}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dev"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    env_file: .env
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  pgdata:
```
