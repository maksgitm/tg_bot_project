import logging
import sqlalchemy
from telegram import LabeledPrice, Update
from telegram.ext import (Application, MessageHandler, filters, CommandHandler, ConversationHandler,
                          PreCheckoutQueryHandler)
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from data import db_session
from data.infos import Info

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)
BOT_TOKEN = '6718278003:AAEn1cxM9iKStowSOxMXekv4mrjpl_Dr3YA'
SHOP_TOKEN = '1744374395:TEST:d28241bde3387bace73e'


async def start(update, context):
    markup = ReplyKeyboardMarkup([['🏪 Бот-магазин', '🖥 Бот-обработчик'], ['📋 Список заявок']],
                                 resize_keyboard=True)
    if update.message.chat_id == 5131259861:
        markup = ReplyKeyboardMarkup([['📋 Показать все заявки'], ['☝️ Показать только невыполненные']],
                                     resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text('Начнём работу!', reply_markup=markup)
        return 'show_all_works'
    await update.message.reply_text(
        "👋 Здравствуйте!\n"
        "Через бота Вы можете приобрести другого бота :)\n"
        "Вы можете выбрать категорию бота для покупки или посмотреть "
        "список отправленных заявок для создания бота.\n"
        "🆘 Помощь: /help\n"
        "❌ Отмена действия: /stop", reply_markup=markup
    )
    return 'choice'


async def choice(update, context):
    chat_id = update.message.chat_id
    markup = ReplyKeyboardMarkup([['👌 Да!'], ['🏠 Главное меню']],
                                 one_time_keyboard=True, resize_keyboard=True)
    answer = update.message.text
    if answer == 'Стоп':
        await update.message.reply_text("❌ Действие отменено.\n"
                                        "Нажмите /start, чтобы начать заново.")
        return ConversationHandler.END
    elif answer == '🏪 Бот-магазин':
        await update.message.reply_text('👌 Хорошо!\n'
                                        'С помощью такого бота вы сможете размещать на продажу свои товары, '
                                        'а клиент сможет оплачивать их в самом боте!\n'
                                        'Цена бота: 800 рублей\n'
                                        'Продолжить?'
                                        , reply_markup=markup)
        context.user_data['variant'] = 'магазин'

        return 'payment'
    elif answer == '🖥 Бот-обработчик':
        await update.message.reply_text('👍 Отлично!\n'
                                        'Благодаря такому боту можно обрабатывать данные пользователя. Например, '
                                        'бот-переводчик или бот, умеющий преобразовывать '
                                        'изображения в другие форматы.\n'
                                        'Цена бота: 500 рублей\n'
                                        'Продолжить?',
                                        reply_markup=markup)
        context.user_data['variant'] = 'обработчик'
        return 'payment'
    elif answer == '📋 Список заявок':
        db_sess = db_session.create_session()
        for work in db_sess.query(Info).filter(Info.user_id == chat_id).all():
            work_id = f"Заявка №{work.id}\n"
            description = work.description
            status = f"Статус: {work.status}"
            await context.bot.send_message(chat_id=chat_id, text=f"{work_id}{description}\n{status}")


async def payment_check(update, context):
    query = update.pre_checkout_query
    if query.invoice_payload != "Custom-Payload":
        await query.answer(ok=False, error_message="❌ Что-то пошло не так...")
    else:
        await query.answer(ok=True)



async def successful_payment(update, context):
    markup = ReplyKeyboardMarkup([['➡️ Далее']], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text('🥳 Ура! Оплата прошла успешно!\n'
                                    'Чтобы продолжить, нажмите на Далее.', reply_markup=markup)


async def payment(update, context):
    text = update.message.text
    if text == 'Стоп':
        await update.message.reply_text('❌ Действие отменено.\n'
                                        'Нажмите /start, чтобы начать заново.')
        return ConversationHandler.END
    elif text == '🏠 Главное меню':
        markup = ReplyKeyboardMarkup([['🏪 Бот-магазин', '🖥 Бот-обработчик'],
                                      ['📋 Список заявок']],
                                     resize_keyboard=True)
        await update.message.reply_text(
            "Выберите, пожалуйста, действие:", reply_markup=markup
        )
        return 'choice'
    elif text == '👌 Да!':
        markup = ReplyKeyboardMarkup([['🏠 Главное меню']], resize_keyboard=True)
        await update.message.reply_text('👍 Отлично!\n'
                                        'Теперь осталось оплатить бота, а затем отправить техническое '
                                        'задание.', reply_markup=markup)
        chat_id = update.message.chat_id
        title = "Оплата бота"
        description = "Пожалуйста, оплатите бота."
        payload = "Custom-Payload"
        currency = "rub"
        if context.user_data["variant"] == 'магазин':
            price = 80000
        else:
            price = 50000
        prices = [LabeledPrice("Test", price)]
        await context.bot.send_invoice(chat_id, title, description, payload, SHOP_TOKEN, currency, prices)
        return 'asking_description'


async def asking_description(update, context):
    text = update.message.text
    if text == '➡️ Далее':
        await update.message.reply_text('✍️ Расскажите, пожалуйста, о боте в нескольких словах:')
        return 'asking_file'
    elif text == '🏠 Главное меню':
        markup = ReplyKeyboardMarkup([['🏪 Бот-магазин', '🖥 Бот-обработчик'],
                                      ['📋 Список заявок']], resize_keyboard=True)
        await update.message.reply_text(
            "Выберите действие:", reply_markup=markup
        )
        return 'choice'


async def asking_file(update, context):
    text = update.message.text
    if text == 'Стоп':
        await update.message.reply_text('❌ Действие отменено.\n'
                                        'Нажмите /start, чтобы начать заново.')
        return ConversationHandler.END
    elif text:
        context.user_data["description"] = text
        await update.message.reply_text('🙌 Отлично!\n'
                                        'Теперь нужно отправить разработчику ТЗ (техническое задание) '
                                        'в одном из предложенных форматах: ".docx", ".doc", ".txt", '
                                        '".rtf", ".odt", ".pdf".\n'
                                        'В ТЗ необходимо указать все функции, которые вы желали бы увидеть в '
                                        'телеграм-боте. Также можете добавить примечания к боту.')
        return 'getting_file'


async def getting_file(update, context):
    markup = ReplyKeyboardMarkup([['🏪 Бот-магазин', '🖥 Бот-обработчик'], ['📋 Список заявок']],
                                 resize_keyboard=True)
    user_id = update.message.chat_id
    file = await context.bot.get_file(update.message.document)
    file_format = file.file_path.split('/')[-1].split('.')[-1]
    if (file_format == 'doc' or file_format == 'docx' or file_format == 'txt' or file_format == 'rtf' or
            file_format == 'odt' or file_format == 'pdf') and file.file_size != 0:
        await file.download_to_drive(f"files/send_file.{file_format}")
    else:
        await update.message.reply_text('❌Неверный формат файла')
    with open(f"files/send_file.{file_format}", 'rb') as file:
        tt_file = file.read()
    db_sess = db_session.create_session()
    try:
        info = Info(
            user_id=user_id,
            ad_data=tt_file,
            type=context.user_data["variant"],
            format=file_format,
            description=context.user_data["description"]
        )
        db_sess.add(info)
        db_sess.commit()
    except sqlalchemy.exc.IntegrityError:
        await update.message.reply_text('ℹ️ Вы уже добавили файл')

    work = db_sess.query(Info).order_by(Info.id.desc()).first()
    work_id = f"Заявка №{work.id}\n"
    user_id = f"id пользователя: {work.user_id}\n"
    data = work.ad_data
    description = f"Описание: {work.description}\n"
    await context.bot.send_message(chat_id=5131259861, text=f"{work_id}{description}{user_id}")
    with open(f"files/file_{work.id}.{work.format}", 'wb') as ff:
        ff.write(data)
    f = open(f"files/file_{work.id}.{work.format}", 'rb')
    await context.bot.send_document(chat_id=5131259861, document=f)
    f.close()

    await update.message.reply_text('✅ Заявка на создание бота успешно подана!\nКогда бот будет готов, '
                                    'будет отправлено его короткое имя.', reply_markup=markup)
    return 'choice'


async def show_all_works(update, context):
    text = update.message.text
    markup = ReplyKeyboardMarkup([['✉️ Отправить бота пользователю'], ['◀️ Назад']],
                                 resize_keyboard=True, one_time_keyboard=True)
    if text == '📋 Показать все заявки' or text == '☝️ Показать только невыполненные':
        db_sess = db_session.create_session()
        for work in db_sess.query(Info).all():
            work_id = f"Заявка №{work.id}\n"
            user_id = f"ID пользователя: {work.user_id}\n"
            description = f"Описание: {work.description}\n"
            status = f"Статус: {work.status}\n"
            with open(f"files/file_{work.id}.{work.format}", 'wb') as ff:
                ff.write(work.ad_data)
            if text == '☝️ Показать только невыполненные':
                if work.status == 'В работе':
                    await context.bot.send_message(chat_id=5131259861, text=f"{work_id}{description}"
                                                   f"{user_id}{status}",
                                                   reply_markup=markup)
                    f = open(f"files/file_{work.id}.{work.format}", 'rb')
                    await context.bot.send_document(chat_id=5131259861, document=f)
                    f.close()
            else:
                await context.bot.send_message(chat_id=5131259861, text=f"{work_id}{description}"
                                                                        f"{user_id}{status}",
                                               reply_markup=markup)
                f = open(f"files/file_{work.id}.{work.format}", 'rb')
                await context.bot.send_document(chat_id=5131259861, document=f)
                f.close()
        send_text = '⬇️ Чтобы отправить готового бота пользователю, нажмите на кнопку ниже'
        await context.bot.send_message(chat_id=5131259861, text=send_text)
        return 'send_bot_preparing'


async def send_bot_preparing(update, context):
    text = update.message.text
    markup = ReplyKeyboardMarkup([['📋 Показать все заявки'], ['☝️ Показать только невыполненные']],
                                 resize_keyboard=True, one_time_keyboard=True)
    if text == "✉️ Отправить бота пользователю":
        await update.message.reply_text('ℹ️ Чтобы отправить бота пользователю, '
                                        'введите имя бота и номер заявки в формате @<имя бота>, <номер заявки>')
        return 'send_bot_finish'
    elif text == '◀️ Назад':
        await update.message.reply_text(text='Выберите действие:', reply_markup=markup)
        return 'show_all_works'


async def send_bot_finish(update, context):
    text = update.message.text
    markup = ReplyKeyboardMarkup([['📋 Показать все заявки'], ['☝️ Показать только невыполненные']],
                                 resize_keyboard=True, one_time_keyboard=True)
    if text == '◀️ Назад':
        await update.message.reply_text(text='Выберите действие:', reply_markup=markup)
        return 'show_all_works'
    try:
        bot_name, id_ = update.message.text.split(', ')
        db_sess = db_session.create_session()
        work = db_sess.query(Info).get(int(id_))
        work.status = 'Готово'
        user_id = work.user_id
        description = work.description
        db_sess.commit()
        await context.bot.send_message(chat_id=user_id, text=f"✅ Ваш бот готов! (заявка №{int(id_)})\n"
                                       f"{description}\n{bot_name}")
        await update.message.reply_text('✅ Бот успешно отправлен!')
    except Exception:
        await context.bot.send_message(text='❌ Неверный формат', chat_id=update.message.chat_id)


async def stop(update, context):

    await update.message.reply_text("❌ Действие отменено.\n"
                                    "Нажмите /start, чтобы начать заново.")
    return ConversationHandler.END


async def help(update, context):
    await update.message.reply_text(
        "ℹ️ По всем вопросам обращайтесь: penkovmaks07@gmail.com"
    )


def main():
    db_session.global_init("db/tg_bot_db.sqlite")
    application = Application.builder().token("6718278003:AAEn1cxM9iKStowSOxMXekv4mrjpl_Dr3YA").build()
    application.add_handler(CommandHandler("help", help))
    application.add_handler(PreCheckoutQueryHandler(payment_check))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    conv_handler_user = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            "choice": [MessageHandler(filters.TEXT & ~filters.COMMAND, choice)],
            "payment": [MessageHandler(filters.TEXT & ~filters.COMMAND, payment)],
            "asking_description": [MessageHandler(filters.TEXT & ~filters.COMMAND, asking_description)],
            "asking_file": [MessageHandler(filters.TEXT & ~filters.COMMAND, asking_file)],
            "getting_file": [MessageHandler(filters.Document.ALL & ~filters.COMMAND, getting_file)],

            "show_all_works": [MessageHandler(filters.TEXT & ~filters.COMMAND, show_all_works)],
            "send_bot_preparing": [MessageHandler(filters.TEXT & ~filters.COMMAND, send_bot_preparing)],
            "send_bot_finish": [MessageHandler(filters.TEXT & ~filters.COMMAND, send_bot_finish)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    application.add_handler(conv_handler_user)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
