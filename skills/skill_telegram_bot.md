# Skill: Telegram Bot (aiogram 3.x)

## Stack
- **Framework:** aiogram 3.x (async, event-driven)
- **FSM:** MemoryStorage o RedisStorage para flujos multi-paso
- **DB:** SQLite (pequeño) o PostgreSQL (producción)
- **Deploy:** Docker + polling o webhook (nginx)

## Estructura de directorios
```
bot/
├── main.py              # Arranca el bot
├── handlers/
│   ├── __init__.py
│   ├── start.py         # /start, /help
│   ├── commands.py      # Comandos principales
│   └── callbacks.py     # InlineKeyboard callbacks
├── states/
│   └── forms.py         # FSM States
├── keyboards/
│   ├── inline.py        # InlineKeyboardMarkup builders
│   └── reply.py         # ReplyKeyboardMarkup builders
├── services/
│   └── db.py            # Lógica de negocio / DB
└── config.py            # TOKEN, ALLOWED_IDS, etc.
```

## Patrones obligatorios

### Setup base
```python
from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)
```

### Handler con FSM
```python
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class OrderForm(StatesGroup):
    name = State()
    phone = State()

@router.message(Command("order"))
async def start_order(msg: Message, state: FSMContext):
    await state.set_state(OrderForm.name)
    await msg.answer("¿Cuál es tu nombre?")

@router.message(OrderForm.name)
async def process_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await state.set_state(OrderForm.phone)
    await msg.answer("¿Tu teléfono?")
```

### InlineKeyboard
```python
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Ver pedidos", callback_data="orders")
    builder.button(text="⚙️ Ajustes", callback_data="settings")
    builder.adjust(2)
    return builder.as_markup()
```

### Callback handler
```python
from aiogram.types import CallbackQuery

@router.callback_query(lambda c: c.data == "orders")
async def show_orders(callback: CallbackQuery):
    await callback.answer()  # Quita el loading
    await callback.message.edit_text("Tus pedidos:", reply_markup=orders_kb())
```

## Seguridad
- Validar `chat_id` en handlers sensibles
- Rate limiting manual con dict + timestamp
- NUNCA ejecutar código del usuario directamente
