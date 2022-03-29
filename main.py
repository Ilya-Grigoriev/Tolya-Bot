from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup
import requests
from datetime import datetime


def first_response(update, context):
    update.message.reply_text('Введите название города:')
    return 1


def start(update, context):
    reply_keyboard = [['/forecast']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(
        f'Привет, {update.message["chat"]["first_name"]}. Меня зовут Толя! У меня следующий набор функций:',
        reply_markup=markup)


def translate(text, from_lang, to_lang):
    url = "https://translated-mymemory---translation-memory.p.rapidapi.com/api/get"
    direct = f'{from_lang}|{to_lang}'
    querystring = {"langpair": direct, "q": text, "mt": "1", "onlyprivate": "0", "de": "a@b.c"}
    headers = {
        'x-rapidapi-key': "850ab61210msh591f51e046aed36p1f65bcjsn098691cd7941",
        'x-rapidapi-host': "translated-mymemory---translation-memory.p.rapidapi.com"
    }
    response = requests.request("GET", url, headers=headers, params=querystring).json()
    return response['responseData']['translatedText']


def forecast(update, context):
    place = update.message['text']
    apikey = '40d1649f-0493-4b70-98ba-98533de7710b'
    geocoder_request = f'http://geocode-maps.yandex.ru/1.x/?apikey={apikey}&geocode="{place}"&format=json'
    response = requests.get(geocoder_request)
    if response:
        json_response = response.json()
        pos = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]['Point']['pos']
        lon, lat = pos.split()
    else:
        print("Ошибка выполнения запроса:")
        print(geocoder_request)
        print("Http статус:", response.status_code, "(", response.reason, ")")
    headers = {'lat': lat, 'lon': lon, 'lang': 'ru_RU',
               'X-Yandex-API-Key': '9009f2a9-7220-4bb5-be28-0fad1d330b93'}
    response = requests.get('https://api.weather.yandex.ru/v2/forecast?', headers=headers).json()
    print(response)
    ts = int(response['now'])
    date = datetime.utcfromtimestamp(ts).strftime('%d.%m.%Y')
    temp = response['fact']['temp']
    feels_temp = response['fact']['feels_like']
    condition = translate(response['fact']['condition'], 'en', 'ru')
    pressure = response['fact']['pressure_mm']
    humidity = response['fact']['humidity']
    wind_speed = response['fact']['wind_speed']
    update.message.reply_text(f'Прогноз погоды сегодня в городе {place.capitalize()} на {date}:')
    update.message.reply_text(f'Температура: {temp}℃')
    update.message.reply_text(f'Ощущаемая температура: {feels_temp}℃')
    update.message.reply_text(f'Погодное описание: {condition.lower()}')
    update.message.reply_text(f'Давление: {pressure} мм')
    update.message.reply_text(f'Влажность: {humidity}%')
    update.message.reply_text(f'Скорость ветра {wind_speed} м/с.')


def stop(update, context):
    update.message.reply_text('Программа завершена', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    token = '5147228144:AAG-lIcg7-YZJqpJ5gfHZrR_J6hBtAZomO0'
    updater = Updater(token)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('forecast', first_response)],
        states={
            1: [MessageHandler(Filters.text & (~ Filters.command), forecast)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
