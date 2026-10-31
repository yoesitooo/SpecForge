# Skill: Seguridad en APIs
## Triggers: auth, jwt, seguridad, security, autenticacion

### Checklist de Seguridad Obligatorio

**1. Autenticación:**
- [ ] JWT con expiración corta (access: 30min, refresh: 7 días)
- [ ] Nunca guardar JWT en localStorage (usar httpOnly cookies)
- [ ] Validar firma del token en cada request

**2. Inputs:**
- [ ] Sanitizar TODOS los campos antes de DB
- [ ] Validar tipos con Pydantic en FastAPI
- [ ] Límite de longitud en todos los campos de texto

**3. CORS:**
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tudominio.com"],  # NUNCA "*" en producción
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

**4. Rate Limiting:**
- Implementar límite de requests por IP (especialmente en login)
- Usar `slowapi` para FastAPI

**5. Variables de Entorno:**
- NUNCA hardcodear secrets en el código
- Usar `.env` + `python-dotenv`
- `.env` siempre en `.gitignore`
