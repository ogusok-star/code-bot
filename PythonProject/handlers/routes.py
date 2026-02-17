from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton, 
)
from aiogram.fsm.context import FSMContext
from forms.user import Form

router = Router()

REGISTERED_USERS = set()

def back_inline():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back")]
        ]
    )

def phone_reply():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отправить номер", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if user_id in REGISTERED_USERS:
        await message.answer(
            "Привет, вижу вы зарегистрированы, давайте работать!"
        )
        return


    if await state.get_state() is not None:
        await message.answer(" Сначала завершите регистрацию")
        return

    msg = await message.answer(
        " Привет,для использования бота пройдите регестрацию!\n\nВведите ваше имя:",
        parse_mode="Markdown",
        reply_markup=back_inline()
    )

    await state.update_data(msg_id=msg.message_id)
    await state.set_state(Form.name)


@router.message(Form.name, F.text)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    data = await state.get_data()

    try:
        await message.delete()
    except:
        pass

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data["msg_id"],
        text="Введите вашу фамилию:",
        parse_mode="Markdown",
        reply_markup=back_inline()
    )

    await state.set_state(Form.firstname)


@router.message(Form.firstname, F.text)
async def process_firstname(message: Message, state: FSMContext):
    await state.update_data(firstname=message.text)
    data = await state.get_data()

    try:
        await message.delete()
    except:
        pass

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data["msg_id"],
        text="Отправьте ваш номер телефона:",
        parse_mode="Markdown",
        reply_markup=back_inline()
    )

    await message.answer(
        "Нажмите кнопку ниже",
        reply_markup=phone_reply()
    )

    await state.set_state(Form.phone)

@router.message(Form.phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    contact = message.contact

    if contact.user_id != message.from_user.id:
        await message.answer(" Отправьте свой номер телефона")
        return

    await state.update_data(phone=contact.phone_number)
    data = await state.get_data()

    REGISTERED_USERS.add(message.from_user.id)

    try:
        await message.delete()
    except:
        pass

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data["msg_id"],
        text=(
            " НЕВЕРОЯТНЫЙ УСПЕХ!\nпроверьте данные\n"
            f"Имя: {data['name']}\n"
            f"Фамилия: {data['firstname']}\n"
            f"Телефон: {data['phone']}"
        ),
        parse_mode="Markdown"
    )

    await state.clear()


@router.message(Form.phone, F.text)
async def block_phone_text(message: Message):
    try:
        await message.delete()
    except:
        pass

@router.callback_query(F.data == "back")
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get("msg_id")
    current_state = await state.get_state()

    if current_state == Form.firstname:
        await state.set_state(Form.name)
        text = "Введите ваше имя:"

    elif current_state == Form.phone:
        await state.set_state(Form.firstname)
        text = "Введите вашу фамилию:"

        await call.answer("")
    else:
        return

    await call.message.bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=msg_id,
        text=text,
        parse_mode="Markdown",
        reply_markup=back_inline()
    )

    await call.answer()