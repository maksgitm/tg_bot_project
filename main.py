from requests import get
import logging
import aiohttp
import telegram
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, ChatMemberAdministrator
from data import db_session
from data.infos import Info

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)
BOT_TOKEN = '6718278003:AAEn1cxM9iKStowSOxMXekv4mrjpl_Dr3YA'
bot = Bot(token=BOT_TOKEN)


async def test(update, context):
    answer = update.message.text
    if answer == 'Разместить рекламу':
        await update.message.reply_text('Успешно!')
        return 2
    elif answer == 'Добавить канал':
        await update.message.reply_text('END')
        return ConversationHandler.END
    # elif update.message.text == 'Добавить канал':


async def test2(update, context):
    await update.message.reply_text('END')
    return ConversationHandler.END


async def get_response(url, params):
    logger.info(f"getting {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            return await resp.json()


async def unset(update, context):
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Таймер отменен!' if job_removed else 'У вас нет активных таймеров'
    await update.message.reply_text(text)


async def task(context):
    await context.bot.send_message(context.job.chat_id, text=f'КУКУ! {context.job.data} c. прошли!')


def remove_job_if_exists(name, context):
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def set_timer(update, context):
    try:
        chat_id = update.effective_message.chat_id
        time = float(context.args[0])
        if time < 0:
            await update.effective_message.reply_text('Нельзя установить таймер на отрицательное время :(')
            return

        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_once(task, time, chat_id=chat_id, name=str(chat_id), data=time)

        text = f'Вернусь через {time} с.!'
        if job_removed:
            text += ' Старая задача удалена.'
        await update.effective_message.reply_text(text)
    except (ValueError, IndexError):
        await update.effective_message.reply_text('Установите время в секундах')


async def close_keyboard(update, context):
    await update.message.reply_text(
        "Ok",
        reply_markup=ReplyKeyboardRemove()
    )


async def start(update, context):
    shop_btn = InlineKeyboardButton('Бот-магазин', callback_data='shop')
    other_btn = InlineKeyboardButton(text='Бот-обработчик', callback_data='other')
    markup = InlineKeyboardMarkup([[shop_btn],
                                   [other_btn]])
    await update.message.reply_text(
        "Здравствуйте!\n"
        "Через бота Вы можете приобрести другого бота :)\n"
        "Выберите,  пожалуйста, категорию бота:", reply_markup=markup
    )
    return 0


async def write_data(update, context):
    db_sess = db_session.create_session()
    info = Info()
    info.ad_data = context.args[0]
    db_sess.add(info)
    db_sess.commit()


async def read_data(update, context):
    db_sess = db_session.create_session()
    info = db_sess.query(Info).all()
    items = [item.to_dict() for item in info]
    items = [item["ad_data"] for item in items]
    print(items)
    await update.effective_message.reply_text(items)


# Теперь только через ReplyKeyboardMarkup!!!!!!
async def second(update, context):
    query = update.callback_query
    await query.answer()
    # keyboard = [[InlineKeyboardButton(text='123', callback_data='12')], [InlineKeyboardButton(text='2', callback_data='12')]]
    # markup = InlineKeyboardMarkup(keyboard)
    if query.data == 'shop':
        # await query.edit_message_text(text='Отлично! Теперь ознакомьтесь с описанием1')
        return 1
    elif query.data == 'other':
        # await query.edit_message_text(text='Отлично! Теперь ознакомьтесь с описанием2', reply_markup=None)


async def third(update, context):
    await update.message.reply_text('Отлично!')


async def first_response_from_owner(update, context):
    answer = update.message.text
    if answer == 'Стоп':
        await update.message.reply_text("Действие отменено.\n"
                                        "Нажмите /start, чтобы начать заново.")
        return ConversationHandler.END
    elif answer == 'Разместить рекламу':
        await update.message.reply_text('Успешно!')
        # return 2
    elif answer == 'Добавить канал':
        await update.message.reply_text("Отлично!\n"
                                        "Добавьте, пожалуйста, этого бота (@for_testing_my_program_bot) к себе в канал "
                                        "и назначьте администратором, а также разрешите делать публикации. Затем "
                                        "отправьте боту имя канала в формате @<уникальное имя вашего канала>.\n"
                                        "Для отмены действия нажмите /stop.")
        return 'channel_1'


async def second_response_from_owner(update, context):
    channel_name = update.message.text
    user_id = update.message.chat_id
    if channel_name == 'Стоп':
        await update.message.reply_text("Действие отменено.\n"
                                        "Нажмите /start, чтобы начать заново.")
        return ConversationHandler.END
    try:
        response = get(f"https://api.telegram.org/bot6718278003:AAEn1cxM9iKStowSOxMXekv4m"
                       f"rjpl_Dr3YA/getChat?chat_id={channel_name}").json()
        channel_id = response["result"]["id"]
        admins = await bot.get_chat_administrators(channel_id)
        check_lst = []
        for admin in admins:
            check_lst.append(admin.user.id)
        if user_id not in check_lst:
            await update.message.reply_text("Извините! Вы не являетесь администратором этого канала.\n"
                                            "Попробуйте ещё раз, нажав /start.")
            return ConversationHandler.END
        else:
            await update.message.reply_text(f"Отлично! Вы добавили канал {channel_name}\n"
                                            f"Теперь введите, пожалуйста, стоимость одного поста в рублях.")
            return 'channel_2'
    except KeyError:
        await update.message.reply_text("Извините, такого канала не существует.\n"
                                        "Попробуйте ещё раз, нажав /start.")
        return ConversationHandler.END
    except telegram.error.BadRequest:
        await update.message.reply_text("Извините! Вы не являетесь администратором этого канала.\n"
                                        "Попробуйте ещё раз, нажав /start.")
        return ConversationHandler.END


async def stop(update, context):
    await update.message.reply_text("Действие отменено.\n"
                                    "Нажмите /start, чтобы начать заново.")
    return ConversationHandler.END


async def help(update, context):
    await update.message.reply_text(
        "Я бот справочник.")


def main():
    db_session.global_init("db/tg_example.sqlite")
    application = Application.builder().token("6718278003:AAEn1cxM9iKStowSOxMXekv4mrjpl_Dr3YA").build()
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("close", close_keyboard))
    application.add_handler(CommandHandler("set", set_timer))
    application.add_handler(CommandHandler("unset", unset))

    conv_handler = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /start. Она задаёт первый вопрос.
        entry_points=[CommandHandler('start', start)],

        # Состояние внутри диалога.
        # Вариант с двумя обработчиками, фильтрующими текстовые сообщения.
        states={
            0: [CallbackQueryHandler(second)],
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, third)],
            "channel_1": [MessageHandler(filters.TEXT & ~filters.COMMAND, second_response_from_owner)],
            # "channel_2": [MessageHandler(filters.TEXT & ~filters.COMMAND, third_response_from_owner)]
        },

        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop)]
    )

    application.add_handler(conv_handler)

    application.run_polling()


if __name__ == '__main__':
    main()
