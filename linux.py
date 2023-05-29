import logging

from typing import List, Tuple, cast, Union
from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, PicklePersistence, InvalidCallbackData, MessageHandler, filters

# Определяем переменную для включения/отключения логирования
enable_logging = False

# Если логирование включено, то выполняем настройку
if enable_logging:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )

# Создаем логгер
logger = logging.getLogger(__name__)

TOKEN = '5606907397:AAGETKPCS-PUw7lUWbqNtiQe6pEuXSTDoIQ'


answerOptions = {
    'project': ['BTC6X',
                'Coinzix',
                'Counos',
                'Dex-Trade',
                'BitStorage',
                'Alterdice',
                'Emirex.com',
                'Emirex.ee',
                'FalconX69'],

    'lang': ["EN", "RU"],

    'duration': ['Short', 'Long']
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(text='Please, select project name:', reply_markup=build_keyboard('project'))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text(
        "Use /start to test this bot. Use /clear to clear the stored data so that you can see "
        "what happens, if the button data is not available. "
    )


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clears the callback data cache"""
    context.bot.callback_data_cache.clear_callback_data()
    context.bot.callback_data_cache.clear_callback_queries()
    await update.effective_message.reply_text("All clear!")


def build_keyboard(keyboard_name: str) -> InlineKeyboardMarkup:
    """Helper function to build the next inline keyboard."""
    if keyboard_name not in answerOptions:
        raise ValueError("Invalid keyboard_name: {}".format(keyboard_name))

    current_list = answerOptions[keyboard_name]

    return InlineKeyboardMarkup.from_column(
        [InlineKeyboardButton(str(current_list[i]), callback_data={
            'actionName': keyboard_name,
            'answer': current_list[i]
        }) for i in range(len(current_list))]
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    actionName, answer = query.data.get('actionName'), query.data.get('answer')

    if actionName == "project":
        await select_project(update, context, answer)
    elif actionName == "lang":
        await select_language(update, context, answer)
    elif actionName == "duration":
        await select_duration(update, context, answer)


async def select_project(update: Update, context: ContextTypes.DEFAULT_TYPE, project: str) -> None:
    query = update.callback_query
    context.user_data['project'] = project
    await query.edit_message_text(
        text=f"Project selected: {project}.\nChoose language please:",
        reply_markup=build_keyboard('lang'),
    )


async def select_language(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str) -> None:
    query = update.callback_query
    context.user_data['lang'] = lang
    projectName = context.user_data['project']
    await query.edit_message_text(
        text=f"Project selected: {projectName}.\nLanguage selected: {lang}.\nChoose maintenance duration:",
        reply_markup=build_keyboard('duration'),
    )


async def select_duration(update: Update, context: ContextTypes.DEFAULT_TYPE, duration: str) -> None:
    query = update.callback_query
    projectName = context.user_data['project']
    lang = context.user_data['lang']

    context.user_data['duration'] = duration
    context.user_data['nextActionName'] = 'get_reason_message'
    await query.edit_message_text(
        text=f"Enter the reason for switching the project into maintenance mode:",
    )


async def select_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reason_text = update.message.text
    context.user_data['reason_text'] = reason_text
    context.user_data['nextActionName'] = 'get_timeIn_message'

    await update.message.reply_text("Enter the time of entry into maintenance mode:")


async def select_timeIn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    timeIn_text = update.message.text
    context.user_data['timeIn_text'] = timeIn_text
    context.user_data['nextActionName'] = 'get_timeOut_message'

    await update.message.reply_text("Enter the time of exit from maintenance mode:")


async def select_timeOut(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    timeOut_text = update.message.text
    context.user_data['timeOut_text'] = timeOut_text
    context.user_data['nextActionName'] = "None"
    await send_report(update, context)


async def read_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    nextActionName = context.user_data['nextActionName']

    if nextActionName == 'get_reason_message':
        await select_reason(update, context)

    if nextActionName == 'get_timeIn_message':
        await select_timeIn(update, context)

    if nextActionName == 'get_timeOut_message':
        await select_timeOut(update, context)


async def send_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    params = context.user_data
    messages = generate_text(
        params["lang"],
        params["project"],
        params["duration"],
        params["timeIn_text"],
        params["reason_text"],
        # Используйте метод get для получения значения timeOut_text, чтобы обработать случай отсутствия этого ключа в словаре.
        params.get("timeOut_text")
    )
    await update.message.reply_text(display_text(messages))


def display_text(text_list):
    text = "\n".join(text_list)
    return text


def generate_text(lang: str, project: str, duration: str, timeIn_text: str, reason_text: str, timeOut_text: str = None) -> Union[str, list]:
    valid_langs = answerOptions['lang']
    lang = lang.upper() if lang.upper() in valid_langs else valid_langs[0]

    language_mappings = {
        'EN': {
            'PROJECT': 'Project',
            'MAINTENANCE_ENTRY': 'Time of entry into Maintenance',
            'MAINTENANCE_EXIT': 'Time of exit',
            'REASON': 'Reason',
            'MAINTENANCE_EXITED': 'MAINTENANCE FINISHED',
            'MAINTENANCE_START': 'MAINTENANCE STARTED',
        },
        'RU': {
            ''
            'PROJECT': 'Проект',
            'MAINTENANCE_ENTRY': 'Время введения в мейнтененс',
            'MAINTENANCE_EXIT': 'Время вывода',
            'REASON': 'Причина',
            'MAINTENANCE_EXITED': 'МЕЙНТЕНЕНС ЗАКОНЧЕН',
            'MAINTENANCE_START': 'НАЧАЛО МЕЙНТЕНЕНСА',
        }
    }

    if duration == "Short":
        text = [
            f"{language_mappings[lang]['MAINTENANCE_START']}",
            f"{language_mappings[lang]['PROJECT']}: {project}",
            f"{language_mappings[lang]['MAINTENANCE_ENTRY']}: {timeIn_text}",
            f"{language_mappings[lang]['MAINTENANCE_EXIT']}: {timeOut_text}",
            f"{language_mappings[lang]['REASON']}: {reason_text}"
        ]
        return text

    if duration == 'Long':
        text = [
            f"{language_mappings[lang]['MAINTENANCE_START']}",

            f"{language_mappings[lang]['PROJECT']}: {project}",
            f"{language_mappings[lang]['MAINTENANCE_ENTRY']}: {timeIn_text}",
            f"{language_mappings[lang]['REASON']}: {reason_text}",

            f"\n",
            
            f"{language_mappings[lang]['MAINTENANCE_EXITED']}",

            f"{language_mappings[lang]['PROJECT']}: {project}",
            f"{language_mappings[lang]['MAINTENANCE_EXIT']}: {timeOut_text}",
        ]
        return text


async def handle_invalid_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Informs the user that the button is no longer available."""
    await update.callback_query.answer()
    await update.effective_message.edit_text(
        "Sorry, I could not process this button click 😕 Please send /start to get a new keyboard."
    )


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    persistence = PicklePersistence(filepath="arbitrarycallbackdatabot")
    application = Application.builder().token(
        TOKEN).persistence(persistence).arbitrary_callback_data(True).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))

    application.add_handler(
        CallbackQueryHandler(handle_invalid_button,
                             pattern=InvalidCallbackData)
    )
    application.add_handler(CallbackQueryHandler(callback_handler))

    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, read_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()

while True:
    try:
        bot.infinity_polling()    
    except Exception as e:
        time.sleep(3)