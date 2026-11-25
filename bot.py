import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- НАСТРОЙКИ ---
BOT_TOKEN = "9129925793:AAElP5CdQmQFIChGsaWa7hK6PWVGo0CKUm8"
PROVIDER_TOKEN = "381764678:TEST:197340"

# Товары: название, описание и цена в КОПЕЙКАХ (не в рублях!)
PRODUCTS = {
    "product_1": {"title": "Товар 1 (Базовый)", "description": "Описание первого товара", "price": 10000}, # 100.00 руб.
    "product_2": {"title": "Товар 2 (Про)", "description": "Описание второго товара", "price": 25000}  # 250.00 руб.
}

logging.basicConfig(level=logging.INFO)

# Создаем бота (теперь напрямую, без прокси)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- КЛАВИАТУРА С ТОВАРАМИ ---
def get_products_keyboard():
    builder = InlineKeyboardBuilder()
    for key, product in PRODUCTS.items():
        builder.button(
            text=f"{product['title']} — {product['price'] / 100:.2f} руб.",
            callback_data=f"buy:{key}"
        )
    builder.adjust(1) # Кнопки в один столбец
    return builder.as_markup()

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Добро пожаловать в магазин! Выберите товар для покупки:",
        reply_markup=get_products_keyboard()
    )

@dp.callback_query(F.data.startswith("buy:"))
async def process_buy(callback: CallbackQuery):
    product_key = callback.data.split(":")[1]
    product = PRODUCTS.get(product_key)
    if not product:
        await callback.answer("Товар не найден.")
        return

    # Отправляем счёт на оплату
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=product["title"],
        description=product["description"],
        payload=f"order_{product_key}_{callback.from_user.id}", # Уникальный идентификатор заказа
        provider_token=PROVIDER_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label=product["title"], amount=product["price"])],
        # Данные для чека (требование 54-ФЗ, можно оставить так для теста)
        provider_data='{"receipt": {"items": [{"description": "' + product["title"] + '", "quantity": "1.00", "amount": {"value": "' + f"{product['price'] / 100:.2f}" + '", "currency": "RUB"}, "vat_code": 1}]}}'
    )
    await callback.answer()

# Обязательный обработчик: подтверждаем готовность принять оплату
@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# Обработчик успешной оплаты
@dp.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payment_info = message.successful_payment
    await message.answer(
        f"✅ Платеж на сумму {payment_info.total_amount / 100:.2f} руб. прошел успешно!\n"
        f"Ваш заказ: {payment_info.invoice_payload}"
    )
    # Здесь можно добавить логику выдачи товара (например, отправку файла или ссылки)

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
