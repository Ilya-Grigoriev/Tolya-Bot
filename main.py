from telegram.ext import Updater, MessageHandler, Filters, CommandHandler


def start(update, context):
    update.message.reply_text(
        f'Привет, {update.message["chat"]["first_name"]}. Меня зовут Толя! У меня следующий набор функций:')


def main():
    token = '5147228144:AAG-lIcg7-YZJqpJ5gfHZrR_J6hBtAZomO0'
    updater = Updater(token)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    updater.start_polling()
    updater.idle()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()
