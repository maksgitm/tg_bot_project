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


async def start(update, context):
    markup = ReplyKeyboardMarkup([['Бот-магазин'],
                                  ['Бот-обработчик']], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Здравствуйте!\n"
        "Через бота Вы можете приобрести другого бота :)\n"
        "Выберите,  пожалуйста, категорию бота:", reply_markup=markup
    )
    return 0


async def back_start(update, context):
    pass


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


async def first_response_from_owner(update, context):
    markup = ReplyKeyboardMarkup([['Да!'], ['Назад']],
                                 one_time_keyboard=True, resize_keyboard=True)
    answer = update.message.text
    if answer == 'Стоп':
        await update.message.reply_text("Действие отменено.\n"
                                        "Нажмите /start, чтобы начать заново.")
        return ConversationHandler.END
    elif answer == 'Бот-магазин':
        await update.message.reply_text('Хорошо!\n'
                                        'С помощью такого бота вы сможете размещать на продажу свои товары, '
                                        'а клиент сможет оплачивать их в самом боте!\n'
                                        'Цена бота: 800 рублей.'
                                        'Продолжить?'
                                        , reply_markup=markup)
        return 'shop_1'
    elif answer == 'Бот-обработчик':
        await update.message.reply_text('Отлично!\n'
                                        'Благодаря такому боту можно обрабатывать данные пользователя. Например, '
                                        'бот-переводчик или бот, умеющий преобразовывать '
                                        'изображения в другие форматы.\n'
                                        'Цена бота: 500 рублей.'
                                        'Продолжить?',
                                        reply_markup=markup)
        return 'other_1'


async def get_TT_from_owner(update, context):
    # try:
    file = await context.bot.get_file(update.message.document)
    await file.download_to_drive(file.file_name + update.message.chat_id)
    # except


async def second_response_shop(update, context):
    text = update.message.text
    if text == 'Стоп':
        await update.message.reply_text('Действие отменено.\n'
                                        'Нажмите /start, чтобы начать заново.')
        return ConversationHandler.END
    elif text == 'Да!':
        await update.message.reply_text('Замечательно!\n'
                                        'Теперь нужно отправить разработчику ТЗ (техническое задание) в формате ... . '
                                        'В нём необходимо указать все функции, которые вы желали бы увидеть в вашем '
                                        'телеграм-боте. Также можете добавить примечания к боту.')
        return 'shop_2'
    elif text == 'Назад':
        markup = ReplyKeyboardMarkup([['Бот-магазин'],
                                      ['Бот-обработчик']], one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            "Выберите, пожалуйста, категорию бота:", reply_markup=markup
        )
        return 0


async def second_response_other(update, context):
    pass


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
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, first_response_from_owner)],
            "shop_1": [MessageHandler(filters.TEXT & ~filters.COMMAND, second_response_shop)],
            'back_start': [MessageHandler(filters.TEXT & ~filters.COMMAND, back_start)],
            "other_1": [MessageHandler(filters.TEXT & ~filters.COMMAND, second_response_other)],
            # "channel_2": [MessageHandler(filters.TEXT & ~filters.COMMAND, third_response_from_owner)]
        },

        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop)]
    )

    application.add_handler(conv_handler)

    application.run_polling()


if __name__ == '__main__':
    main()
