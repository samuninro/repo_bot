import html
import os
from dataclasses import dataclass
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InputMediaPhoto
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

load_dotenv()

# ======================
# НАСТРОЙКИ / СПРАВОЧНИКИ
# ======================

USERS_FILE = "allowed_users.txt"
BOT_PASSWORD = "1234"

def load_allowed_users():
    if not os.path.exists(USERS_FILE):
        return set()
    with open(USERS_FILE, "r") as f:
        return {int(line.strip()) for line in f if line.strip()}
def save_user(user_id: int):
    with open(USERS_FILE, "a") as f:
        f.write(f"{user_id}\n")





CONTRACTOR = 'ООО "РОКС-ЦЕНТР"'

# Объекты пока как 1..10 (как ты просил).
# Позже можно заменить значения на реальные названия объектов.
OBJECTS = [
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10"
]


MOGE_STATUSES = [
    "Получено положительное заключение",
    "На рассмотрении",
    "Корректировка",
]

SYSTEM_OPTIONS = ["2-трубная", "4-трубная"]
PIPE_OPTIONS = ["Сталь ППУ", "ГПИ"]
LAYING_OPTIONS = ["Бесканальная", "Канальная", "Надземная"]


@dataclass(frozen=True)
class Responsible:
    fio: str
    position: str
    phone: str


# ЗАГЛУШКИ ответственных — замени на свои реальные данные
RESPONSIBLES = [
    Responsible("Иванов Иван Иванович", "Прораб", "+7 (900) 000-00-01"),
    Responsible("Петров Пётр Петрович", "Нач. участка", "+7 (900) 000-00-02"),
    Responsible("Сидоров Сидор Сидорович", "Инженер", "+7 (900) 000-00-03"),
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
    ("Выполнение работ по Перекрытию каналов / Запесочивание", "м. п."),
    ("Обратная засыпка", "шт."),
    ("Выполнение работ по благоустройству", "м^2"),
]


def plan_work_keyboard(selected: set[int]):
    kb = InlineKeyboardBuilder()

    for i, text in enumerate(PLAN_WORK_OPTIONS):
        prefix = "✅ " if i in selected else ""
        kb.button(
            text=f"{prefix}{text}",
            callback_data=f"planopt:{i}"
        )

    kb.button(text="➡️ Готово", callback_data="planopt:done")
    kb.adjust(1)
    return kb.as_markup()

def fact_work_keyboard(selected: set[int]):
    kb = InlineKeyboardBuilder()
    for i, (text, unit) in enumerate(FACT_WORK_OPTIONS):
        prefix = "✅ " if i in selected else ""
        # можно показывать единицы прямо в кнопке, чтобы люди сразу понимали
        kb.button(text=f"{prefix}{text} ({unit})", callback_data=f"factopt:{i}")
    kb.button(text="➡️ Готово", callback_data="factopt:done")
    kb.adjust(1)
    return kb.as_markup()


# ======================
# FSM (состояния анкеты)
# ======================

class ReportForm(StatesGroup):
    enter_password = State() # пароль
    choosing_object = State()
    choosing_moge = State()

    plan_work_adding = State()

    resources_people = State()
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
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ======================

def kb_from_list(items: list[str], prefix: str, cols: int = 1):
    """
    Строит inline-клавиатуру: каждая кнопка -> callback_data = f"{prefix}:{index}"
    """
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

def ensure_int(text: str) -> int | None:
    text = text.strip()
    if not text.isdigit():
        return None
    return int(text)

def format_report(data: dict) -> str:
    """
    Формирует итоговый текст отчёта в HTML (для Telegram).
    """
    def esc(x) -> str:
        return html.escape(str(x)) if x is not None else ""

    today = datetime.now().strftime("%d.%m.%Y")

    obj_text = esc(data.get("object", "(не указан)"))
    moge = esc(data.get("moge", "(не указан)"))

    plan_items = data.get("plan_items", [])
    people = esc(data.get("people", ""))
    machines = esc(data.get("machines", ""))

    # ---- Факт с единицами ----
    fact_selected = data.get("fact_selected", [])
    fact_values = data.get("fact_values", {})

    fact_lines = []
    for idx in fact_selected:
        text, unit = FACT_WORK_OPTIONS[idx]
        v = fact_values.get(str(idx), "")
        # Ед.изм. показываем ровно так, как у тебя
        fact_lines.append(f"• {esc(text)}: <b>{esc(v)}</b> {esc(unit)}")
    fact_block = "\n".join(fact_lines) if fact_lines else "—"

    # ---- План ----
    plan_lines = [f"• {esc(x)}" for x in plan_items] if plan_items else ["—"]
    plan_block = "\n".join(plan_lines)

    # ---- Тепловые сети ----
    total_len = esc(data.get("heat_total_length", ""))
    system = esc(data.get("heat_system", ""))
    pipe = esc(data.get("heat_pipe", ""))
    laying = esc(data.get("heat_laying", ""))

    done_demont = esc(data.get("done_demont", ""))
    done_mont = esc(data.get("done_mont", ""))
    done_welds = esc(data.get("done_welds", ""))

    left_demont = esc(data.get("left_demont", ""))
    left_mont = esc(data.get("left_mont", ""))
    left_welds = esc(data.get("left_welds", ""))

    materials_total = esc(data.get("materials_total", ""))

    resp: Responsible | None = data.get("responsible_obj")
    if resp:
        resp_block = (
            f"• ФИО: <b>{esc(resp.fio)}</b>\n"
            f"• Должность: <b>{esc(resp.position)}</b>\n"
            f"• Телефон: <b>{esc(resp.phone)}</b>"
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
        f"• Персонал: <b>{people}</b> чел.\n"
        f"• Техника: <b>{machines}</b> ед.\n\n"

        f"<b>4️⃣ Фактически выполненные работы за прошедшие сутки</b>\n"
        f"{fact_block}\n\n"

        f"━━━━━━━━━━━━━━━━━━━\n"
        f"<b><u>ТЕПЛОВЫЕ СЕТИ</u></b>\n\n"

        f"<b>5️⃣ Общие характеристики</b>\n"
        f"• Протяженность сети (общая): <b>{total_len}</b> п.м.\n"
        f"• Система: <b>{system}</b>\n"
        f"• Тип трубы: <b>{pipe}</b>\n"
        f"• Способ прокладки: <b>{laying}</b>\n\n"

        f"<b>6️⃣ Выполнено за сутки</b>\n"
        f"• Демонтировано: <b>{done_demont}</b> п.м.\n"
        f"• Смонтировано: <b>{done_mont}</b> п.м.\n"
        f"• Сварные стыки: <b>{done_welds}</b> шт.\n\n"

        f"<b>7️⃣ Осталось выполнить</b>\n"
        f"• Демонтировать: <b>{left_demont}</b> п.м.\n"
        f"• Смонтировать: <b>{left_mont}</b> п.м.\n"
        f"• Сварные стыки: <b>{left_welds}</b> шт.\n\n"

        f"<b>8️⃣ Материалы</b>\n"
        f"• Материала всего на объекте (включая смонтированный): <b>{materials_total}</b> п.м.\n\n"

        f"<b>9️⃣ Ответственный</b>\n"
        f"{resp_block}\n"
    )

    return report



async def start_new_report(state: FSMContext):
    """
    Сбрасываем старые данные и начинаем заново.
    """
    await state.clear()
    await state.set_state(ReportForm.choosing_object)


# ======================
# ХЕНДЛЕРЫ
# ======================

async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if user_id not in AUTHORIZED_USERS:
        await state.set_state(ReportForm.enter_password)
        await message.answer("🔐 Введите пароль для доступа:")
        return

    await start_new_report(state)
    await message.answer(
        "<b>Шаг 1: Выберите объект:</b>",
        reply_markup=kb_from_list(OBJECTS, prefix="obj", cols=1)
    )


async def cmd_new(message: Message, state: FSMContext):
    await cmd_start(message, state)

async def password_received(message: Message, state: FSMContext):
    if message.text == BOT_PASSWORD:
        user_id = message.from_user.id

        if user_id not in AUTHORIZED_USERS:
            AUTHORIZED_USERS.add(user_id)
            save_user(user_id)

        await message.answer("✅ Доступ разрешён.")
        await start_new_report(state)
        return

    await message.answer("❌ <b>Неверный пароль.</b>\n\n<b>Для доступа пришлите 1000р. по номеру <i>89852242520</i> СберБанк</b>")


async def obj_chosen(call: CallbackQuery, state: FSMContext):
    idx = int(call.data.split(":")[1])
    await state.update_data(object=OBJECTS[idx])

    await state.set_state(ReportForm.choosing_moge)
    await call.message.edit_text(
        "<b>Шаг 2:\n\n🚧Выберите статус МОГЭ:️</b>",
        reply_markup=kb_from_list(MOGE_STATUSES, prefix="moge", cols=1)
    )
    await call.answer()

async def moge_chosen(call: CallbackQuery, state: FSMContext):
    idx = int(call.data.split(":")[1])
    await state.update_data(moge=MOGE_STATUSES[idx])

    # инициализируем выбранные пункты
    await state.update_data(plan_selected=set())
    await state.set_state(ReportForm.plan_work_adding)

    await call.message.edit_text(
        "<b>Шаг 3:\n\n🪏План работ на текущий день.</b>\n\n"
        "<i>Отметь один или несколько пунктов и нажми «Готово».</i>",
        reply_markup=plan_work_keyboard(set())
    )
    await call.answer()

    async def plan_option_chosen(call: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        selected: set[int] = data.get("plan_selected", set())

        action = call.data.split(":")[1]

        if action == "done":
            plan_items = [PLAN_WORK_OPTIONS[i] for i in sorted(selected)]
            await state.update_data(plan_items=plan_items)

            await state.set_state(ReportForm.resources_people)
            await call.message.edit_text(
                "<b>Шаг 4:\n\nРесурсы на объекте.</b>\n\n🦺<b>Введите количество персонала:</b>"
            )
            await call.answer()
            return

        idx = int(action)
        if idx in selected:
            selected.remove(idx)
        else:
            selected.add(idx)

        await state.update_data(plan_selected=selected)
        await call.message.edit_reply_markup(
            reply_markup=plan_work_keyboard(selected)
        )
        await call.answer()

   #  async def plan_buttons(call: CallbackQuery, state: FSMContext):
   # action = call.data.split(":")[1]

        if action == "add":
            await call.message.answer("<b>Отправьте текст пункта плана работ одним сообщением.</b>")
            await call.answer()
            return

        if action == "done":
            await state.set_state(ReportForm.resources_people)
            await call.message.edit_text("<b>Шаг 4:\n\nРесурсы на объекте.</b>\n\n<b>🦺Введите количество персонала:</b>")
            await call.answer()
            return

#async def plan_item_received(message: Message, state: FSMContext):
 #   data = await state.get_data()
  #  items = data.get("plan_items", [])
   # items.append(message.text.strip())
    #await state.update_data(plan_items=items)

    # await message.answer(f"✅ Добавлено. Сейчас в плане {len(items)} пункт(ов).")

async def resources_people_received(message: Message, state: FSMContext):
    val = ensure_int(message.text)
    if val is None:
        await message.answer("<b>Введите число!</b>\n\n (например: 12).")
        return
    await state.update_data(people=val)
    await state.set_state(ReportForm.resources_machines)
    await message.answer("<b>🚜Введите количество техники:</b>")

async def resources_machines_received(message: Message, state: FSMContext):
    val = ensure_int(message.text)
    if val is None:
        await message.answer("<b>Введите число!</b>\n\n(например: 3).")
        return
    await state.update_data(machines=val)

    # Фактически выполненные работы: сначала выбор пунктов
    await state.update_data(fact_selected=[], fact_values={}, fact_current=0)
    await state.set_state(ReportForm.fact_work_adding)

    await message.answer(
        "<b>Шаг 5:\n\n✅Фактически выполненные работы за прошедшие сутки.</b>\n\n"
        "<i>Отметь один или несколько пунктов и нажми «Готово».</i>",
        reply_markup=fact_work_keyboard(set())
    )

    # await message.answer(
    #     "<b>Шаг 5:✅\n\nФактически выполненные работы за прошедшие сутки.</b>\n"
    #     "Добавляй пункты по одному сообщению.",
    #     reply_markup=kb.as_markup()
    # )

    # if action == "add":
    #     await call.message.answer("<b>Отправьте текст пункта фактически выполненных работ одним сообщением.</b>")
    #     await call.answer()
    #     return

    # if action == "done":
    #     await state.set_state(ReportForm.heat_total_length)
    #     await call.message.edit_text("<b>Шаг 6:\n\n🔥Тепловые сети — протяженность сети (общая), п.м.:</b>")
    #     await call.answer()
    #     return

async def heat_total_length_received(message: Message, state: FSMContext):
    val = ensure_int(message.text)
    if val is None:
        await message.answer("Нужно ввести число (например: 120).")
        return
    await state.update_data(heat_total_length=val)
    await state.set_state(ReportForm.heat_system)
    await message.answer("<b>Система:</b>", reply_markup=kb_from_list(SYSTEM_OPTIONS, "sys", cols=2))

async def heat_system_chosen(call: CallbackQuery, state: FSMContext):
    idx = int(call.data.split(":")[1])
    await state.update_data(heat_system=SYSTEM_OPTIONS[idx])
    await state.set_state(ReportForm.heat_pipe)
    await call.message.edit_text("<b>Тип трубы:</b>", reply_markup=kb_from_list(PIPE_OPTIONS, "pipe", cols=2))
    await call.answer()

async def heat_pipe_chosen(call: CallbackQuery, state: FSMContext):
    idx = int(call.data.split(":")[1])
    await state.update_data(heat_pipe=PIPE_OPTIONS[idx])
    await state.set_state(ReportForm.heat_laying)
    await call.message.edit_text("<b>Способ прокладки:</b>", reply_markup=kb_from_list(LAYING_OPTIONS, "lay", cols=1))
    await call.answer()

async def heat_laying_chosen(call: CallbackQuery, state: FSMContext):
    idx = int(call.data.split(":")[1])
    await state.update_data(heat_laying=LAYING_OPTIONS[idx])

    await state.set_state(ReportForm.done_demont)
    await call.message.edit_text("<b>Выполнено за сутки:\n\n🪏Демонтировано (п.м.):</b>")
    await call.answer()

async def num_received(message: Message, state: FSMContext, field: str, next_state: State, prompt: str):
    val = ensure_int(message.text)
    if val is None:
        await message.answer("<b>Введите число!</b>")
        return
    await state.update_data(**{field: val})
    await state.set_state(next_state)
    await message.answer(prompt)

async def done_demont_received(message: Message, state: FSMContext):
    await num_received(message, state, "done_demont", ReportForm.done_mont,"<b>Выполнено за сутки\n\n💪🏻Смонтировано (п.м.):</b>")

async def done_mont_received(message: Message, state: FSMContext):
    await num_received(message, state, "done_mont", ReportForm.done_welds, "<b>Выполнено за сутки\n\n🪢Сварные стыки (шт.):</b>")

async def done_welds_received(message: Message, state: FSMContext):
    await num_received(message, state, "done_welds", ReportForm.left_demont, "<b>Осталось выполнить\n\n🪏Демонтировать (п.м.):</b>")

async def left_demont_received(message: Message, state: FSMContext):
    await num_received(message, state, "left_demont", ReportForm.left_mont, "<b>Осталось выполнить\n\n💪🏻Смонтировать (п.м.):</b>")

async def left_mont_received(message: Message, state: FSMContext):
    await num_received(message, state, "left_mont", ReportForm.left_welds, "<b>Осталось выполнить\n\n🪢Сварные стыки (шт.):</b>")

async def left_welds_received(message: Message, state: FSMContext):
    await num_received(message, state, "left_welds", ReportForm.materials_total, "<b>🏗️Материала всего на объекте (п.м.):</b>")

async def materials_total_received(message: Message, state: FSMContext):
    val = ensure_int(message.text)
    if val is None:
        await message.answer("<b>Введите число!</b>")
        return
    await state.update_data(materials_total=val)

    await state.set_state(ReportForm.responsible_choose)
    await message.answer("<b>Шаг 7:\n\n📝Выберите ответственного:</b>", reply_markup=kb_from_list(
        [f"{r.fio} — {r.position}" for r in RESPONSIBLES],
        "resp",
        cols=1
    ))

async def responsible_chosen(call: CallbackQuery, state: FSMContext):
    idx = int(call.data.split(":")[1])
    resp = RESPONSIBLES[idx]
    await state.update_data(responsible_obj=resp)

    data = await state.get_data()
    report_text = format_report(data)
    await state.update_data(report_text=report_text)

    # переходим к сбору медиа
    await state.update_data(media_photo_ids=[], media_video_ids=[])
    await state.set_state(ReportForm.media_collecting)

    await call.message.edit_text(
        "<b>📎 Шаг 8: Фото/видео</b>\n\n"
        "Прикрепи <b>фото и/или видео</b> (можно несколько).\n"
        "Когда закончишь — нажми <b>«Готово»</b>.\n\n"
        "<i>Если медиа не нужно — нажми «Пропустить».</i>",
        reply_markup=kb_media_done_skip()
    )
    await call.answer()

async def confirm(call: CallbackQuery, state: FSMContext):
    decision = call.data.split(":")[1]
    data = await state.get_data()

    if decision == "yes":
        photo_ids = data.get("media_photo_ids", [])
        video_ids = data.get("media_video_ids", [])

        # Фото — альбомами по 10
        if photo_ids:
            rest = photo_ids[:]
            while rest:
                chunk = rest[:10]
                rest = rest[10:]
                media = [InputMediaPhoto(media=pid) for pid in chunk]
                await call.message.answer_media_group(media)

        # Видео — по одному
        for vid in video_ids:
            await call.message.answer_video(vid)

        # Текст отчёта
        await call.message.answer(data["report_text"])

        # Новый отчёт
        await start_new_report(state)
        await call.message.answer(
            "<b>Шаг 1: Выберите объект:</b>",
            reply_markup=kb_from_list(OBJECTS, prefix="obj", cols=1)
        )
        await call.answer()
        return

    if decision == "no":
        await state.clear()
        await call.message.edit_text("❌ Отменено. Напиши /new чтобы начать заново.")
        await call.answer()
        return


async def plan_option_chosen(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    # ВАЖНО: вместо set храним list (надёжнее, если потом решишь хранить в Redis/JSON)
    selected = set(data.get("plan_selected", []))

    action = call.data.split(":")[1]

    if action == "done":
        plan_items = [PLAN_WORK_OPTIONS[i] for i in sorted(selected)]
        await state.update_data(plan_items=plan_items)

        await state.set_state(ReportForm.resources_people)
        await call.message.edit_text(
            "<b>Шаг 4:\n\nРесурсы на объекте.</b>\n\n<b>🦺Введите количество персонала:</b>"
        )
        await call.answer()
        return

    idx = int(action)
    if idx in selected:
        selected.remove(idx)
    else:
        selected.add(idx)

    await state.update_data(plan_selected=sorted(selected))
    await call.message.edit_reply_markup(
        reply_markup=plan_work_keyboard(selected)
    )
    await call.answer()



async def fact_option_chosen(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = set(data.get("fact_selected", []))

    action = call.data.split(":")[1]

    if action == "done":
        selected_list = sorted(selected)
        await state.update_data(fact_selected=selected_list, fact_values={}, fact_current=0)

        if not selected_list:
            # если ничего не выбрали — можно разрешить пропуск (или заставить выбрать)
            await call.answer("Выбери хотя бы один пункт.", show_alert=True)
            return

        # переходим к поочередному вводу цифр
        await state.set_state(ReportForm.fact_work_filling)
        first_idx = selected_list[0]
        text, unit = FACT_WORK_OPTIONS[first_idx]

        await call.message.edit_text(
            f"<b>Введи объём/количество для:</b>\n\n"
            f"<b>• {text}</b>\n"
            f"Ед. изм.: <b>{unit}</b>\n\n"
            f"<i>(Только цифра:)</i>"
        )
        await call.answer()
        return

    idx = int(action)
    if idx in selected:
        selected.remove(idx)
    else:
        selected.add(idx)

    await state.update_data(fact_selected=sorted(selected))
    await call.message.edit_reply_markup(reply_markup=fact_work_keyboard(selected))
    await call.answer()




async def fact_value_received(message: Message, state: FSMContext):
    val = ensure_int(message.text)
    if val is None:
        await message.answer("<b>Нужно ввести только цифру.</b>")
        return

    data = await state.get_data()
    selected: list[int] = data.get("fact_selected", [])
    values: dict = data.get("fact_values", {})
    cur: int = data.get("fact_current", 0)

    # записали значение для текущего пункта
    current_idx = selected[cur]
    values[str(current_idx)] = val

    # двигаемся дальше
    cur += 1
    await state.update_data(fact_values=values, fact_current=cur)

    # если все заполнены — идем к тепловым сетям
    if cur >= len(selected):
        await state.set_state(ReportForm.heat_total_length)
        await message.answer("<b>Шаг 6:\n\n🔥Тепловые сети — протяженность сети (общая), п.м.:</b>\n<i>(только цифра)</i>")
        return

    # иначе спрашиваем следующий пункт
    next_idx = selected[cur]
    text, unit = FACT_WORK_OPTIONS[next_idx]

    text = html.escape(text)
    unit = html.escape(unit)

    await message.answer(
        f"<b>Введи объём/количество для:</b>\n\n"
        f"• <b>{text}</b>\n"
        f"Ед. изм.: <b>{unit}</b>\n\n"
        f"<i>(Только цифра)</i>"
    )




async def media_received(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_ids = data.get("media_photo_ids", [])
    video_ids = data.get("media_video_ids", [])

    # Фото: берём самое большое (последнее)
    if message.photo:
        photo_ids.append(message.photo[-1].file_id)
        await state.update_data(media_photo_ids=photo_ids)
        await message.answer(f"✅ Фото добавлено (всего: {len(photo_ids)}).")
        return

    # Видео
    if message.video:
        video_ids.append(message.video.file_id)
        await state.update_data(media_video_ids=video_ids)
        await message.answer(f"✅ Видео добавлено (всего: {len(video_ids)}).")
        return

    await message.answer("Можно отправлять только фото или видео. Когда закончишь — нажми «Готово».")

async def media_done(call: CallbackQuery, state: FSMContext):
    action = call.data.split(":")[1]
    data = await state.get_data()

    # и "Готово", и "Пропустить" ведут к превью
    await state.set_state(ReportForm.preview)
    await call.message.edit_text(
        f"{data['report_text']}\n\n<b>Подтвердить?</b>",
        reply_markup=kb_yes_no()
    )
    await call.answer()
# ======================
# =======ПАРОЛЬ

# ======================
# ТОЧКА ВХОДА
# ======================

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Не найден BOT_TOKEN. Создай .env и укажи BOT_TOKEN=...")

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode="HTML")
    )

    global AUTHORIZED_USERS
    AUTHORIZED_USERS = load_allowed_users()

    dp = Dispatcher()

    # Команды
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_new, Command("new"))

    # Выбор объекта / МОГЭ
    dp.callback_query.register(obj_chosen, F.data.startswith("obj:"), ReportForm.choosing_object)
    dp.callback_query.register(moge_chosen, F.data.startswith("moge:"), ReportForm.choosing_moge)

    # План работ

    dp.callback_query.register(plan_option_chosen,F.data.startswith("planopt:"),ReportForm.plan_work_adding)

    # Ресурсы
    dp.message.register(resources_people_received, ReportForm.resources_people)
    dp.message.register(resources_machines_received, ReportForm.resources_machines)

    # Факт работ
    dp.callback_query.register(
        fact_option_chosen,
        F.data.startswith("factopt:"),
        ReportForm.fact_work_adding
    )

    dp.message.register(fact_value_received, ReportForm.fact_work_filling)

    # Тепловые сети
    dp.message.register(heat_total_length_received, ReportForm.heat_total_length)
    dp.callback_query.register(heat_system_chosen, F.data.startswith("sys:"), ReportForm.heat_system)
    dp.callback_query.register(heat_pipe_chosen, F.data.startswith("pipe:"), ReportForm.heat_pipe)
    dp.callback_query.register(heat_laying_chosen, F.data.startswith("lay:"), ReportForm.heat_laying)

    dp.message.register(done_demont_received, ReportForm.done_demont)
    dp.message.register(done_mont_received, ReportForm.done_mont)
    dp.message.register(done_welds_received, ReportForm.done_welds)

    dp.message.register(left_demont_received, ReportForm.left_demont)
    dp.message.register(left_mont_received, ReportForm.left_mont)
    dp.message.register(left_welds_received, ReportForm.left_welds)

    dp.message.register(materials_total_received, ReportForm.materials_total)

    # Ответственный
    dp.callback_query.register(responsible_chosen, F.data.startswith("resp:"), ReportForm.responsible_choose)

    # Подтверждение
    dp.callback_query.register(confirm, F.data.startswith("confirm:"), ReportForm.preview)

    # Фотографии/видео
    dp.message.register(media_received, ReportForm.media_collecting)
    dp.callback_query.register(media_done, F.data.startswith("media:"), ReportForm.media_collecting)

    #Пароль
    dp.message.register(password_received, ReportForm.enter_password)

    # Запуск
    dp.run_polling(bot)



if __name__ == "__main__":
    main()
