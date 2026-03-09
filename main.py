import html
import os
import re

from dataclasses import dataclass
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InputMediaPhoto, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

load_dotenv()

# ======================
# НАСТРОЙКИ
# ======================

USERS_FILE = "allowed_users.txt"
BOT_PASSWORD = os.getenv("BOT_PASSWORD", "1234")
CONTRACTOR = 'ООО "РОКС-ЦЕНТР"'

AUTHORIZED_USERS: set[int] = set()


# ======================
# СПРАВОЧНИКИ
# ======================

DIRECTIONS = {
    "Электросталь": [
        'Выполнение работ и оказание услуг, связанных с одновременным выполнением инженерных изысканий, подготовкой проектной документации, разработкой рабочей документации, выполнением работ по капитальному ремонту тепловых сетей по мероприятию: "Капитальный ремонт участков тепловой сети от ТК-25 до ТК-26, от ТК-24 до ТК-23, от ТК-21 до ТК-33, от ТК-21 до ТК-17 по ул. К.Маркса, от ТК-17 до ТК-9 по ул. Октябрьская, от ТК-51 до ТК-13 по ул. Захарченко в г.о. Электросталь (в т.ч. ПИР)"',
        'Выполнение работ и оказание услуг, связанных с одновременным выполнением инженерных изысканий, подготовкой проектной документации, разработкой рабочей документации, выполнением работ по капитальному ремонту тепловых сетей по мероприятию: "Капитальный ремонт участков тепловой сети от опуска до ТК-322, от У-54 через ТК-368а до ввода в д. 47Б по ул. Спортивная в г.о. Электросталь (в т.ч. ПИР)"',
        'Выполнение работ и оказание услуг, связанных с одновременным выполнением инженерных изысканий, подготовкой проектной документации, разработкой рабочей документации, выполнением работ по капитальному ремонту тепловых сетей по мероприятию: "Капитальный ремонт участков тепловой сети от ТК-155 до ТК-363а, от ТК-155 до ТК366, от ТК-406 до ТК-254 по ул. Спортивная, от ТК-163 до ТК-206, от ТК-162 до ТК-163 по ул. Корнеева, от ТК-161 до ТК-252а по ул. Загонова, от ТК-203 до ТК-161 по ул. Мичурина, от ТК-165а до ТК-168 по ул. К. Маркса в г.о. Электросталь (в т.ч. ПИР)"',
        'Выполнение работ и оказание услуг, связанных с одновременным выполнением инженерных изысканий, подготовкой проектной документации, разработкой рабочей документации, выполнением работ по капитальному ремонту тепловых сетей по мероприятию: "Сети теплоснабжения и горячего водоснабжения в п. Новые дома, г.о. Электросталь (в т.ч. ПИР)"',
    ],
    "Зарайск": [
        'Выполнение работ и оказание услуг, связанных с одновременным выполнением инженерных изысканий, подготовкой проектной документации, разработкой рабочей документации, выполнением работ по реконструкции по мероприятию: «Реконструкция сетей теплоснабжения г. Зарайск, школа № 6 до ул. Ленинской (в т.ч. ПИР)»; «Реконструкция сетей теплоснабжения г. Зарайск ул. Комсомольская ж.д. №32 до ж.д. №85 ул. Дзержинского (в т.ч. ПИР)»',
        'Выполнение работ и оказание услуг, связанных с одновременным выполнением инженерных изысканий, подготовкой проектной документации, разработкой рабочей документации, выполнением работ по реконструкции по мероприятию: «Реконструкция сетей теплоснабжения г. Зарайск пос. ПМК от котельной ПМК (в т.ч. ПИР)»',
        'Выполнение работ и оказание услуг, связанных с одновременным выполнением инженерных изысканий, подготовкой проектной документации, разработкой рабочей документации, выполнением работ по реконструкции по мероприятию: "Реконструкция сети теплоснабжения и горячего водоснабжения д. Алферьево (в т.ч. ПИР)"',
        'Выполнение работ и оказание услуг, связанных с одновременным выполнением инженерных изысканий, подготовкой проектной документации, разработкой рабочей документации, выполнением работ по реконструкции по мероприятию: "Реконструкция сетей теплоснабжения и горячего водоснабжения м.о. Зарайск, д. Зименки (в т.ч. ПИР)"',
    ],
    "Лосино-Петровский": [
        'Выполнение работ и оказание услуг, связанных с одновременным выполнением инженерных изысканий, подготовкой проектной документации, разработкой рабочей документации, выполнением работ по строительству по мероприятию: «Строительство участков тепловых сетей от зданий по адресу: Московская области, г.о. Лосино-Петровский, ул. Горького 15, 17, 19, 21, 23, Чехова 4, 8, Гоголя 3, 5, 7, 8, Октябрьская 16, 18, 20, 24а, до ЦТП 2 котельной по адресу: г.о. Лосино-Петровский, ул. Гоголя, 31 (в т.ч. ПИР)»',
        'Выполнение работ и оказание услуг, связанных с одновременным выполнением инженерных изысканий, подготовкой проектной документации, разработкой рабочей документации, выполнением работ по строительству по мероприятию: «Строительство участков тепловых сетей по адресу: Московская область, г.о. Лосино-Петровский, к зданиям ул. Ленина 10, стр. 1, 2, 3, 4, пл. Революции 24 от котельной ЦГБ и котельной по адресу Гоголя, 31»',
        'Выполнение работ и оказание услуг, связанных с одновременным выполнением инженерных изысканий, подготовкой проектной документации, выполнением работ по строительству по мероприятию: «Строительство участков тепловых сетей от зданий по адресу: Московская область, г.о. Лосино-Петровский, ул. Гоголя 24, 26, 28, 30, Ленина 15/1, 17, 19, 21, 23, Строителей 2, 3, 4, 5, 6, 9, 11, 17 к ЦТП 5 (котельной по адресу ул. Гоголя, стр. 31) (в т.ч. ПИР)»',
    ],
}
DIRECTION_BUTTONS = list(DIRECTIONS.keys())

MOGE_STATUSES = [
    "Получено положительное заключение",
    "На рассмотрении",
    "Корректировка",
    "Подготовка ПД",
]

SYSTEM_OPTIONS = ["2-трубная", "4-трубная"]
PIPE_OPTIONS = ["Сталь ППУ", "ГПИ"]
LAYING_OPTIONS = ["Бесканальная", "Канальная", "Надземная"]


@dataclass(frozen=True)
class Responsible:
    fio: str
    position: str
    phone: str


RESPONSIBLES = [
    Responsible("Решетник А.В.", "Нач. участка", "+7 (926) 877-71-41"),
    Responsible("Гудков Н.Н.", "Производитель работ", "+7 (964) 718-92-22"),
    Responsible(" Селезнев А.В.", "Производитель работ", "+7 (929) 602-16-19"),
]

PLAN_WORK_OPTIONS = [
    "Разработка грунта механизированным способом",
    "Демонтаж суще-их т/проводов ЦО, ГВС, ХВС, лотков и каналов, камер и т. п.",
    "Монтажные работы по устройству основания под т/проводы",
    "Монолитно-бетонные работы по устройству тепловых камер",
    "Выполнение работ по обвязке тепловых камер",
    "Прокладка трубопроводов ЦО, ГВС, ХВС",
    "Выполнение работ по промывке трубопроводов",
    "Проведение гидравлических испытаний",
    "Выполнение изоляции стыков т/проводов — монтаж СОДК",
    "Изоляция трубопроводов",
    "Выполнение работ по врезке в действующую сеть, камеру",
    "Выполнение работ по врезке потребителей",
    "Запуск в работу проектной т/сети",
    "Работы по монтажу коверов СОДК",
    "Замер сопротивления и сдача СОДК эксплуатирующей организации",
    "Выполнение работ по перекрытию каналов / запесочивание",
    "Обратная засыпка",
    "Выполнение работ по благоустройству",
    "Подготовительные работы",
    "Завоз материалов",
    "Крепление котлованов",
]

FACT_WORK_OPTIONS = [
    ("Разработка грунта механизированным способом", "м^3"),
    ("Демонтаж сущ-их т/проводов ЦО, ГВС, ХВС, лотков и каналов, камер и т.п.", "м.п."),
    ("Монтажные работы по устройству основания под трубопроводы", "м^3"),
    ("Монолитно-бетонных работы по устройству тепловых камер", "м^3"),
    ("Выполнение работ по обвязке тепловых камер", "м^3"),
    ("Прокладка трубопроводов ЦО, ГВС, ХВС", "м.п."),
    ("Выполнение работ по промывке трубопроводов", "шт."),
    ("Проведение гидравлических испытаний", "шт."),
    ("Выполнение изоляции стыков т/проводов - монтаж СОДК", "шт."),
    ("Изоляция трубопроводов", "шт."),
    ("Выполнение работ по врезке в действующую сеть, камеру", "шт."),
    ("Выполнение работ по врезке потребителей", "шт."),
    ("Запуск в работу проектной т/сети", "шт."),
    ("Работы по монтажу коверов СОДК", "шт."),
    ("Замер сопротивления и сдача СОДК эксплуатирующей организации", "шт."),
    ("Выполнение работ по Перекрытию каналов / Запесочивание", "м.п."),
    ("Обратная засыпка", "шт."),
    ("Выполнение работ по благоустройству", "м^2"),
    ("Подготовительные работы", None),
    ("Завоз материалов", None),
    ("Крепление котлованов", None),
]


# ======================
# FSM
# ======================

class ReportForm(StatesGroup):
    enter_password = State()

    choosing_direction = State()
    choosing_object = State()
    choosing_moge = State()

    plan_work_adding = State()

    resources_itr = State()
    resources_workers = State()
    resources_machines = State()

    fact_work_adding = State()
    fact_work_filling = State()

    heat_total_length = State()
    heat_system = State()
    heat_pipe = State()
    heat_laying = State()

    done_demont = State()
    done_mont = State()
    done_welds = State()

    left_demont = State()
    left_mont = State()
    left_welds = State()

    materials_total = State()

    responsible_choose = State()

    media_collecting = State()
    preview = State()


# ======================
# ХРАНИЛИЩЕ ПОЛЬЗОВАТЕЛЕЙ
# ======================

def load_allowed_users() -> set[int]:
    if not os.path.exists(USERS_FILE):
        return set()

    result = set()
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.isdigit():
                result.add(int(line))
    return result


def save_allowed_users(users: set[int]) -> None:
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        for user_id in sorted(users):
            f.write(f"{user_id}\n")


def is_authorized(user_id: int) -> bool:
    return user_id in AUTHORIZED_USERS


# ======================
# КЛАВИАТУРЫ
# ======================

def kb_from_list(items: list[str], prefix: str, cols: int = 1):
    kb = InlineKeyboardBuilder()
    for i, text in enumerate(items):
        kb.button(text=text, callback_data=f"{prefix}:{i}")
    kb.adjust(cols)
    return kb.as_markup()


def kb_yes_no():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить", callback_data="confirm:yes")
    kb.button(text="❌ Отмена", callback_data="confirm:no")
    kb.adjust(2)
    return kb.as_markup()


def kb_media_done_skip():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Готово", callback_data="media:done")
    kb.button(text="⏭ Пропустить", callback_data="media:skip")
    kb.adjust(2)
    return kb.as_markup()


def plan_work_keyboard(selected: set[int]):
    kb = InlineKeyboardBuilder()
    for i, text in enumerate(PLAN_WORK_OPTIONS):
        prefix = "✅ " if i in selected else ""
        kb.button(text=f"{prefix}{text}", callback_data=f"planopt:{i}")
    kb.button(text="➡️ Готово", callback_data="planopt:done")
    kb.adjust(1)
    return kb.as_markup()


def fact_work_keyboard(selected: set[int]):
    kb = InlineKeyboardBuilder()
    for i, (text, unit) in enumerate(FACT_WORK_OPTIONS):
        prefix = "✅ " if i in selected else ""
        btn_text = f"{prefix}{text}" if unit is None else f"{prefix}{text} ({unit})"
        kb.button(text=btn_text, callback_data=f"factopt:{i}")
    kb.button(text="➡️ Готово", callback_data="factopt:done")
    kb.adjust(1)
    return kb.as_markup()

def system_keyboard(selected: set[int]):
    kb = InlineKeyboardBuilder()
    for i, text in enumerate(SYSTEM_OPTIONS):
        prefix = "✅ " if i in selected else ""
        kb.button(text=f"{prefix}{text}", callback_data=f"sysopt:{i}")
    kb.button(text="➡️ Готово", callback_data="sysopt:done")
    kb.adjust(1)
    return kb.as_markup()


def pipe_keyboard(selected: set[int]):
    kb = InlineKeyboardBuilder()
    for i, text in enumerate(PIPE_OPTIONS):
        prefix = "✅ " if i in selected else ""
        kb.button(text=f"{prefix}{text}", callback_data=f"pipeopt:{i}")
    kb.button(text="➡️ Готово", callback_data="pipeopt:done")
    kb.adjust(1)
    return kb.as_markup()


def laying_keyboard(selected: set[int]):
    kb = InlineKeyboardBuilder()
    for i, text in enumerate(LAYING_OPTIONS):
        prefix = "✅ " if i in selected else ""
        kb.button(text=f"{prefix}{text}", callback_data=f"layopt:{i}")
    kb.button(text="➡️ Готово", callback_data="layopt:done")
    kb.adjust(1)
    return kb.as_markup()

# ======================
# УТИЛИТЫ
# ======================



def ensure_non_negative_number(text: str) -> float | None:
    text = text.strip().replace(",", ".")

    match = re.search(r"\d+(\.\d+)?", text)
    if not match:
        return None

    try:
        value = float(match.group())
        return value if value >= 0 else None
    except ValueError:
        return None


def esc(value) -> str:
    return html.escape(str(value)) if value is not None else ""


def format_num(value) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return str(value).replace(".", ",")
    return str(value).replace(".", ",")

def current_date_str() -> str:
    return datetime.now().strftime("%d.%m.%Y")


def toggle_index(current: list[int], idx: int) -> list[int]:
    selected = set(current)
    if idx in selected:
        selected.remove(idx)
    else:
        selected.add(idx)
    return sorted(selected)


def get_responsible_by_index(idx: int | None) -> Responsible | None:
    if idx is None:
        return None
    if 0 <= idx < len(RESPONSIBLES):
        return RESPONSIBLES[idx]
    return None


def format_report(data: dict) -> str:
    today = current_date_str()

    obj_text = esc(data.get("object", "(не указан)"))
    moge = esc(data.get("moge", "(не указан)"))

    plan_items = data.get("plan_items", [])
    itr = data.get("itr", "")
    workers = data.get("workers", "")
    machines = data.get("machines", "")

    fact_selected = data.get("fact_selected", [])
    fact_values = data.get("fact_values", {})

    fact_lines = []
    for idx in fact_selected:
        text, unit = FACT_WORK_OPTIONS[idx]
        value = fact_values.get(str(idx), "")

        if unit is None:
            fact_lines.append(f"• {esc(text)}")
        else:
            fact_lines.append(f"• {esc(text)}: <b>{esc(value)}</b> {esc(unit)}")

    fact_block = "\n".join(fact_lines) if fact_lines else "—"

    plan_lines = [f"• {esc(item)}" for item in plan_items] if plan_items else ["—"]
    plan_block = "\n".join(plan_lines)

    responsible = get_responsible_by_index(data.get("responsible_idx"))
    if responsible:
        resp_block = (
            f"• ФИО: <b>{esc(responsible.fio)}</b>\n"
            f"• Должность: <b>{esc(responsible.position)}</b>\n"
            f"• Телефон: <b>{esc(responsible.phone)}</b>"
        )
    else:
        resp_block = "—"

    report = (
        f"📅 <b>ЕЖЕДНЕВНЫЙ ОТЧЁТ</b>\n"
        f"Дата: <b>{today}</b>\n\n"

        f"<b>1️⃣ Общая информация</b>\n"
        f"• Подрядная организация: <b>{esc(CONTRACTOR)}</b>\n"
        f"• Объект: <b>{obj_text}</b>\n"
        f"• Статус МОГЭ: <b>{moge}</b>\n\n"

        f"<b>2️⃣ План работ на текущий день</b>\n"
        f"{plan_block}\n\n"

    f"<b>3️⃣ Ресурсы на объекте</b>\n"
    f"• ИТР: <b>{esc(format_num(itr))}</b> чел.\n"
    f"• Рабочие: <b>{esc(format_num(workers))}</b> чел.\n"
    f"• Техника: <b>{esc(format_num(machines))}</b> ед.\n\n"

        f"<b>4️⃣ Фактически выполненные работы за прошедшие сутки</b>\n"
        f"{fact_block}\n\n"

        f"━━━━━━━━━━━━━━━━━━━\n"
        f"<b><u>ТЕПЛОВЫЕ СЕТИ</u></b>\n\n"

        f"<b>5️⃣ Общие характеристики</b>\n"
        f"• Протяженность сети (общая): <b>{esc(format_num(data.get('heat_total_length', '')))}</b> п.м.\n"
        f"• Система: <b>{esc(data.get('heat_system', ''))}</b>\n"
        f"• Тип трубы: <b>{esc(data.get('heat_pipe', ''))}</b>\n"
        f"• Способ прокладки: <b>{esc(data.get('heat_laying', ''))}</b>\n\n"

        f"<b>6️⃣ Выполнено за сутки</b>\n"
        f"• Демонтировано: <b>{esc(format_num(data.get('done_demont', '')))}</b> п.м.\n"
        f"• Смонтировано: <b>{esc(format_num(data.get('done_mont', '')))}</b> п.м.\n"
        f"• Сварные стыки: <b>{esc(format_num(data.get('done_welds', '')))}</b> шт.\n\n"

        f"<b>7️⃣ Осталось выполнить</b>\n"
        f"• Демонтировать: <b>{esc(format_num(data.get('left_demont', '')))}</b> п.м.\n"
        f"• Смонтировать: <b>{esc(format_num(data.get('left_mont', '')))}</b> п.м.\n"
        f"• Сварные стыки: <b>{esc(format_num(data.get('left_welds', '')))}</b> шт.\n\n"

        f"<b>8️⃣ Материалы</b>\n"
        f"• Материала всего на объекте (включая смонтированный): "
        f"<b>{esc(format_num(data.get('materials_total', '')))}</b> п.м.\n\n"

        f"<b>9️⃣ Ответственный</b>\n"
        f"{resp_block}\n"
    )
    return report


async def ask_direction(message: Message, state: FSMContext):
    await state.set_state(ReportForm.choosing_direction)
    await message.answer(
        "<b>Привет!👋🏻 Я помогу сформировать ежедневный отчёт.</b>\n\n"
        "<b>Шаг 1: Выберите направление:</b>",
        reply_markup=kb_from_list(DIRECTION_BUTTONS, prefix="dir", cols=1)
    )


async def start_new_report(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(
        plan_selected=[],
        plan_items=[],
        fact_selected=[],
        fact_values={},
        fact_current=0,
        media_photo_ids=[],
        media_video_ids=[],
    )
    await ask_direction(message, state)


async def ask_for_number(
    message: Message,
    state: FSMContext,
    field_name: str,
    next_state: State,
    next_prompt: str,
):
    value = ensure_non_negative_number(message.text)
    if value is None:
        await message.answer("<b>Введите число!</b>")
        return

    await state.update_data(**{field_name: value})
    await state.set_state(next_state)
    await message.answer(next_prompt)


# ======================
# ХЕНДЛЕРЫ АВТОРИЗАЦИИ
# ======================

async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if not is_authorized(user_id):
        await state.clear()
        await state.set_state(ReportForm.enter_password)
        await message.answer("<b>Введите пароль для доступа:</b>")
        return

    await start_new_report(message, state)


async def cmd_new(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if not is_authorized(user_id):
        await state.clear()
        await state.set_state(ReportForm.enter_password)
        await message.answer("<b>Сначала введите пароль:</b>")
        return

    await start_new_report(message, state)


async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Текущее заполнение отменено. Напиши /start чтобы начать заново.")


async def password_received(message: Message, state: FSMContext):
    if message.text == BOT_PASSWORD:
        user_id = message.from_user.id

        if user_id not in AUTHORIZED_USERS:
            AUTHORIZED_USERS.add(user_id)
            save_allowed_users(AUTHORIZED_USERS)

        await message.answer("✅ Доступ разрешён.")
        await start_new_report(message, state)
        return

    await message.answer("❌ <b>Неверный пароль.</b>")


# ======================
# ХЕНДЛЕРЫ ОТЧЁТА
# ======================

async def direction_chosen(call: CallbackQuery, state: FSMContext):
    idx = int(call.data.split(":")[1])
    direction = DIRECTION_BUTTONS[idx]
    objects = DIRECTIONS[direction]

    await state.update_data(direction=direction)
    await state.set_state(ReportForm.choosing_object)

    objects_text = "\n\n".join(
        f"<b>{i + 1}</b> — {html.escape(obj)}"
        for i, obj in enumerate(objects)
    )
    object_buttons = [str(i + 1) for i in range(len(objects))]

    await call.message.edit_text(
        f"<b>Шаг 2: Выберите объект</b>\n\n"
        f"<b>Направление:</b> {html.escape(direction)}\n\n"
        f"{objects_text}",
        reply_markup=kb_from_list(object_buttons, prefix="obj", cols=2)
    )
    await call.answer()


async def obj_chosen(call: CallbackQuery, state: FSMContext):
    idx = int(call.data.split(":")[1])

    data = await state.get_data()
    direction = data["direction"]
    objects = DIRECTIONS[direction]

    await state.update_data(object=objects[idx])
    await state.set_state(ReportForm.choosing_moge)

    await call.message.edit_text(
        "<b>Шаг 3:\n\n🚧 Выберите статус МОГЭ:</b>",
        reply_markup=kb_from_list(MOGE_STATUSES, prefix="moge", cols=1)
    )
    await call.answer()


async def moge_chosen(call: CallbackQuery, state: FSMContext):
    idx = int(call.data.split(":")[1])

    await state.update_data(
        moge=MOGE_STATUSES[idx],
        plan_selected=[],
        plan_items=[],
    )
    await state.set_state(ReportForm.plan_work_adding)

    await call.message.edit_text(
        "<b>Шаг 4:\n\n🪏 План работ на текущий день</b>\n\n"
        "<i>Отметь один или несколько пунктов и нажми «Готово».</i>",
        reply_markup=plan_work_keyboard(set())
    )
    await call.answer()


async def plan_option_chosen(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_selected = data.get("plan_selected", [])
    action = call.data.split(":")[1]

    if action == "done":
        selected_sorted = sorted(current_selected)
        plan_items = [PLAN_WORK_OPTIONS[i] for i in selected_sorted]

        await state.update_data(plan_items=plan_items)

        await state.set_state(ReportForm.resources_itr)

        await call.message.edit_text(
            "<b>Шаг 5:\n\nРесурсы на объекте</b>\n\n"
            "<b>🧑‍💼 Введите количество ИТР:</b>"
        )
        await call.answer()
        return

    idx = int(action)
    updated = toggle_index(current_selected, idx)
    await state.update_data(plan_selected=updated)

    await call.message.edit_reply_markup(
        reply_markup=plan_work_keyboard(set(updated))
    )
    await call.answer()


async def resources_itr_received(message: Message, state: FSMContext):
    value = ensure_non_negative_number(message.text)
    if value is None:
        await message.answer("<b>Введите число!</b>\n\nНапример: 3")
        return

    await state.update_data(itr=value)
    await state.set_state(ReportForm.resources_workers)
    await message.answer("<b>🦺 Введите количество рабочих:</b>")


async def resources_workers_received(message: Message, state: FSMContext):
    value = ensure_non_negative_number(message.text)
    if value is None:
        await message.answer("<b>Введите число!</b>\n\nНапример: 12")
        return

    await state.update_data(workers=value)
    await state.set_state(ReportForm.resources_machines)
    await message.answer("<b>🚜 Введите количество техники:</b>")


async def resources_machines_received(message: Message, state: FSMContext):
    value = ensure_non_negative_number(message.text)
    if value is None:
        await message.answer("<b>Введите число!</b>\n\nНапример: 3")
        return

    await state.update_data(
        machines=value,
        fact_selected=[],
        fact_values={},
        fact_current=0,
    )
    await state.set_state(ReportForm.fact_work_adding)

    await message.answer(
        "<b>Шаг 6:\n\n✅ Фактически выполненные работы за прошедшие сутки</b>\n\n"
        "<i>Отметь один или несколько пунктов и нажми «Готово».</i>",
        reply_markup=fact_work_keyboard(set())
    )


async def fact_option_chosen(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_selected = data.get("fact_selected", [])
    action = call.data.split(":")[1]

    if action == "done":
        selected_list = sorted(current_selected)

        if not selected_list:
            await call.answer("Выбери хотя бы один пункт.", show_alert=True)
            return

        values = {}
        cur = 0

        while cur < len(selected_list):
            idx = selected_list[cur]
            _, unit = FACT_WORK_OPTIONS[idx]
            if unit is None:
                values[str(idx)] = True
                cur += 1
            else:
                break

        await state.update_data(
            fact_selected=selected_list,
            fact_values=values,
            fact_current=cur,
        )

        if cur >= len(selected_list):
            await state.set_state(ReportForm.heat_total_length)
            await call.message.edit_text(
                "<b>Шаг 7:\n\n🔥 Тепловые сети — протяженность сети (общая), п.м.:</b>\n"
                "<i>(только цифра)</i>"
            )
            await call.answer()
            return

        first_idx = selected_list[cur]
        text, unit = FACT_WORK_OPTIONS[first_idx]

        await state.set_state(ReportForm.fact_work_filling)
        await call.message.edit_text(
            f"<b>Введи объём/количество для:</b>\n\n"
            f"• <b>{html.escape(text)}</b>\n"
            f"Ед. изм.: <b>{html.escape(unit)}</b>\n\n"
            f"<i>(только цифра)</i>"
        )
        await call.answer()
        return

    idx = int(action)
    updated = toggle_index(current_selected, idx)
    await state.update_data(fact_selected=updated)

    await call.message.edit_reply_markup(
        reply_markup=fact_work_keyboard(set(updated))
    )
    await call.answer()


async def fact_value_received(message: Message, state: FSMContext):
    value = ensure_non_negative_number(message.text)
    if value is None:
        await message.answer("<b>Нужно ввести только цифру.</b>")
        return

    data = await state.get_data()
    selected: list[int] = data.get("fact_selected", [])
    values: dict = data.get("fact_values", {})
    cur: int = data.get("fact_current", 0)

    current_idx = selected[cur]
    values[str(current_idx)] = value
    cur += 1

    while cur < len(selected):
        next_idx = selected[cur]
        _, unit = FACT_WORK_OPTIONS[next_idx]
        if unit is None:
            values[str(next_idx)] = True
            cur += 1
        else:
            break

    await state.update_data(fact_values=values, fact_current=cur)

    if cur >= len(selected):
        await state.set_state(ReportForm.heat_total_length)
        await message.answer(
            "<b>Шаг 7:\n\n🔥 Тепловые сети — протяженность сети (общая), п.м.:</b>\n"
            "<i>(только цифра)</i>"
        )
        return

    next_idx = selected[cur]
    text, unit = FACT_WORK_OPTIONS[next_idx]

    await message.answer(
        f"<b>Введи объём/количество для:</b>\n\n"
        f"• <b>{html.escape(text)}</b>\n"
        f"Ед. изм.: <b>{html.escape(unit)}</b>\n\n"
        f"<i>(только цифра)</i>"
    )


async def heat_total_length_received(message: Message, state: FSMContext):
    value = ensure_non_negative_number(message.text)
    if value is None:
        await message.answer("<b>Нужно ввести число.</b>\n\nНапример: 120 или 10,5")
        return

    await state.update_data(
        heat_total_length=value,
        heat_system_selected=[]
    )
    await state.set_state(ReportForm.heat_system)
    await message.answer(
        "<b>Система:</b>\n\n<i>Можно выбрать один или несколько вариантов.</i>",
        reply_markup=system_keyboard(set())
    )


async def heat_system_chosen(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_selected = data.get("heat_system_selected", [])
    action = call.data.split(":")[1]

    if action == "done":
        selected_sorted = sorted(current_selected)
        values = [SYSTEM_OPTIONS[i] for i in selected_sorted]

        if not values:
            await call.answer("Выбери хотя бы один вариант.", show_alert=True)
            return

        await state.update_data(
            heat_system_selected=selected_sorted,
            heat_system=", ".join(values),
            heat_pipe_selected=[]
        )
        await state.set_state(ReportForm.heat_pipe)

        await call.message.edit_text(
            "<b>Тип трубы:</b>\n\n<i>Можно выбрать один или несколько вариантов.</i>",
            reply_markup=pipe_keyboard(set())
        )
        await call.answer()
        return

    idx = int(action)
    updated = toggle_index(current_selected, idx)
    await state.update_data(heat_system_selected=updated)

    await call.message.edit_reply_markup(
        reply_markup=system_keyboard(set(updated))
    )
    await call.answer()


async def heat_pipe_chosen(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_selected = data.get("heat_pipe_selected", [])
    action = call.data.split(":")[1]

    if action == "done":
        selected_sorted = sorted(current_selected)
        values = [PIPE_OPTIONS[i] for i in selected_sorted]

        if not values:
            await call.answer("Выбери хотя бы один вариант.", show_alert=True)
            return

        await state.update_data(
            heat_pipe_selected=selected_sorted,
            heat_pipe=", ".join(values),
            heat_laying_selected=[]
        )
        await state.set_state(ReportForm.heat_laying)

        await call.message.edit_text(
            "<b>Способ прокладки:</b>\n\n<i>Можно выбрать один или несколько вариантов.</i>",
            reply_markup=laying_keyboard(set())
        )
        await call.answer()
        return

    idx = int(action)
    updated = toggle_index(current_selected, idx)
    await state.update_data(heat_pipe_selected=updated)

    await call.message.edit_reply_markup(
        reply_markup=pipe_keyboard(set(updated))
    )
    await call.answer()


async def heat_laying_chosen(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_selected = data.get("heat_laying_selected", [])
    action = call.data.split(":")[1]

    if action == "done":
        selected_sorted = sorted(current_selected)
        values = [LAYING_OPTIONS[i] for i in selected_sorted]

        if not values:
            await call.answer("Выбери хотя бы один вариант.", show_alert=True)
            return

        await state.update_data(
            heat_laying_selected=selected_sorted,
            heat_laying=", ".join(values)
        )
        await state.set_state(ReportForm.done_demont)

        await call.message.edit_text(
            "<b>Выполнено за сутки:\n\n🪏 Демонтировано (п.м.):</b>"
        )
        await call.answer()
        return

    idx = int(action)
    updated = toggle_index(current_selected, idx)
    await state.update_data(heat_laying_selected=updated)

    await call.message.edit_reply_markup(
        reply_markup=laying_keyboard(set(updated))
    )
    await call.answer()


async def done_demont_received(message: Message, state: FSMContext):
    await ask_for_number(
        message, state,
        "done_demont",
        ReportForm.done_mont,
        "<b>Выполнено за сутки:\n\n💪🏻 Смонтировано (п.м.):</b>"
    )


async def done_mont_received(message: Message, state: FSMContext):
    await ask_for_number(
        message, state,
        "done_mont",
        ReportForm.done_welds,
        "<b>Выполнено за сутки:\n\n🪢 Сварные стыки (шт.):</b>"
    )


async def done_welds_received(message: Message, state: FSMContext):
    await ask_for_number(
        message, state,
        "done_welds",
        ReportForm.left_demont,
        "<b>Осталось выполнить:\n\n🪏 Демонтировать (п.м.):</b>"
    )


async def left_demont_received(message: Message, state: FSMContext):
    await ask_for_number(
        message, state,
        "left_demont",
        ReportForm.left_mont,
        "<b>Осталось выполнить:\n\n💪🏻 Смонтировать (п.м.):</b>"
    )


async def left_mont_received(message: Message, state: FSMContext):
    await ask_for_number(
        message, state,
        "left_mont",
        ReportForm.left_welds,
        "<b>Осталось выполнить:\n\n🪢 Сварные стыки (шт.):</b>"
    )


async def left_welds_received(message: Message, state: FSMContext):
    await ask_for_number(
        message, state,
        "left_welds",
        ReportForm.materials_total,
        "<b>🏗️ Материала всего на объекте (п.м.):</b>"
    )


async def materials_total_received(message: Message, state: FSMContext):
    value = ensure_non_negative_number(message.text)
    if value is None:
        await message.answer("<b>Введите число!</b>")
        return

    await state.update_data(materials_total=value)
    await state.set_state(ReportForm.responsible_choose)

    await message.answer(
        "<b>Шаг 8:\n\n📝 Выберите ответственного:</b>",
        reply_markup=kb_from_list(
            [f"{r.fio} — {r.position}" for r in RESPONSIBLES],
            "resp",
            cols=1
        )
    )


async def responsible_chosen(call: CallbackQuery, state: FSMContext):
    idx = int(call.data.split(":")[1])

    await state.update_data(
        responsible_idx=idx,
        media_photo_ids=[],
        media_video_ids=[],
    )

    data = await state.get_data()
    report_text = format_report(data)
    await state.update_data(report_text=report_text)

    await state.set_state(ReportForm.media_collecting)
    await call.message.edit_text(
        "<b>📎 Шаг 9: Фото/видео</b>\n\n"
        "Прикрепи <b>фото и/или видео</b> (можно несколько).\n"
        "Когда закончишь — нажми <b>«Готово»</b>.\n\n"
        "<i>Если медиа не нужно — нажми «Пропустить».</i>",
        reply_markup=kb_media_done_skip()
    )
    await call.answer()


async def media_received(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_ids = data.get("media_photo_ids", [])
    video_ids = data.get("media_video_ids", [])

    if message.photo:
        photo_ids.append(message.photo[-1].file_id)
        await state.update_data(media_photo_ids=photo_ids)
        await message.answer(f"✅ Фото добавлено. Всего фото: {len(photo_ids)}")
        return

    if message.video:
        video_ids.append(message.video.file_id)
        await state.update_data(media_video_ids=video_ids)
        await message.answer(f"✅ Видео добавлено. Всего видео: {len(video_ids)}")
        return

    await message.answer(
        "Можно отправлять только фото или видео. Когда закончишь — нажми «Готово»."
    )


async def media_done(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await state.set_state(ReportForm.preview)
    await call.message.edit_text(
        f"{data['report_text']}\n\n<b>Подтвердить?</b>",
        reply_markup=kb_yes_no()
    )
    await call.answer()


async def confirm(call: CallbackQuery, state: FSMContext):
    decision = call.data.split(":")[1]
    data = await state.get_data()

    if decision == "yes":
        photo_ids = data.get("media_photo_ids", [])
        video_ids = data.get("media_video_ids", [])

        if photo_ids:
            rest = photo_ids[:]
            while rest:
                chunk = rest[:10]
                rest = rest[10:]
                media = [InputMediaPhoto(media=pid) for pid in chunk]
                await call.message.answer_media_group(media)

        for vid in video_ids:
            await call.message.answer_video(vid)

        await call.message.answer(data["report_text"])

        await start_new_report(call.message, state)
        await call.answer()
        return

    await state.clear()
    await call.message.edit_text("❌ Отменено. Напиши /new чтобы начать заново.")
    await call.answer()


# ======================
# MAIN
# ======================

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Не найден BOT_TOKEN. Создай .env и укажи BOT_TOKEN=...")

    global AUTHORIZED_USERS
    AUTHORIZED_USERS = load_allowed_users()

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    dp = Dispatcher()

    # Команды
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_new, Command("new"))
    dp.message.register(cmd_cancel, Command("cancel"))

    # Пароль
    dp.message.register(password_received, ReportForm.enter_password)

    # Отчёт
    dp.callback_query.register(direction_chosen, F.data.startswith("dir:"), ReportForm.choosing_direction)
    dp.callback_query.register(obj_chosen, F.data.startswith("obj:"), ReportForm.choosing_object)
    dp.callback_query.register(moge_chosen, F.data.startswith("moge:"), ReportForm.choosing_moge)

    dp.callback_query.register(plan_option_chosen, F.data.startswith("planopt:"), ReportForm.plan_work_adding)

    dp.message.register(resources_itr_received, ReportForm.resources_itr)
    dp.message.register(resources_workers_received, ReportForm.resources_workers)
    dp.message.register(resources_machines_received, ReportForm.resources_machines)

    dp.callback_query.register(fact_option_chosen, F.data.startswith("factopt:"), ReportForm.fact_work_adding)
    dp.message.register(fact_value_received, ReportForm.fact_work_filling)

    dp.message.register(heat_total_length_received, ReportForm.heat_total_length)
    dp.callback_query.register(heat_system_chosen, F.data.startswith("sysopt:"), ReportForm.heat_system)
    dp.callback_query.register(heat_pipe_chosen, F.data.startswith("pipeopt:"), ReportForm.heat_pipe)
    dp.callback_query.register(heat_laying_chosen, F.data.startswith("layopt:"), ReportForm.heat_laying)

    dp.message.register(done_demont_received, ReportForm.done_demont)
    dp.message.register(done_mont_received, ReportForm.done_mont)
    dp.message.register(done_welds_received, ReportForm.done_welds)

    dp.message.register(left_demont_received, ReportForm.left_demont)
    dp.message.register(left_mont_received, ReportForm.left_mont)
    dp.message.register(left_welds_received, ReportForm.left_welds)

    dp.message.register(materials_total_received, ReportForm.materials_total)

    dp.callback_query.register(responsible_chosen, F.data.startswith("resp:"), ReportForm.responsible_choose)

    dp.message.register(media_received, ReportForm.media_collecting)
    dp.callback_query.register(media_done, F.data.startswith("media:"), ReportForm.media_collecting)

    dp.callback_query.register(confirm, F.data.startswith("confirm:"), ReportForm.preview)

    dp.run_polling(bot)


if __name__ == "__main__":
    main()