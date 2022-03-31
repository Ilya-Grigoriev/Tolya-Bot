from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot
import requests
from datetime import datetime
import traceback
import re


def clear_data(context):
    context.user_data['amount'] = None
    context.user_data['from_cur'] = None
    context.user_data['to_cur'] = None
    context.user_data['from_lang'] = None
    context.user_data['to_lang'] = None


def start_keyboard():
    reply_keyboard = [['/forecast', '/converter_currency', '/translate'],
                      ['/spell_check', '/ip_check', '/phone_number_check']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    return markup


def first_response(update, context):
    if update.message['text'] == '/forecast':
        update.message.reply_text('Введите название города:')
    elif update.message['text'] == '/converter_currency':
        update.message.reply_text('Введите количество денег:')
    elif update.message['text'] == '/translate':
        reply_keyboard = [[i] for i in context.user_data['languages']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        update.message.reply_text('Выберите язык, с которого переводите текст:', reply_markup=markup)
    elif update.message['text'] == '/spell_check':
        update.message.reply_text('Введите текст для проверки:')
    elif update.message['text'] == '/ip_check':
        update.message.reply_text('Введите IP-адрес:')
    elif update.message['text'] == '/phone_number_check':
        update.message.reply_text('Введите номер телефона:')
    return 1


def start(update, context):
    with open('currencies.txt', encoding='utf8') as file_1:
        context.user_data['currencies'] = [i.strip('\n') for i in file_1.readlines()]
    context.user_data['languages'] = {'Французский': 'fr', 'Испанский': 'es', 'Русский': 'ru', 'Арабский': 'ar',
                                      'Португальский': 'pt', 'Немецкий': 'de', 'Английский': 'en', 'Китайский': 'zh'}
    update.message.reply_text(
        f'Привет, {update.message["chat"]["first_name"]}. Меня зовут Толя! У меня следующий набор функций:',
        reply_markup=start_keyboard())


# Переводчик
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


# Конвертер валют
def set_amount(update, context):
    try:
        context.user_data['amount'] = float(update.message['text'])
        if context.user_data['amount'] < 0:
            update.message.reply_text('Нельзя вводить отрицательное количество денег')
            update.message.reply_text('Введите количество денег:')
            return 1
        update.message.reply_text('\n'.join(context.user_data['currencies']))
        reply_keyboard = [[i.split()[0]] for i in context.user_data['currencies']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        update.message.reply_text('Выберите валюту, из который переводите деньги:', reply_markup=markup)
        return 2
    except ValueError:
        update.message.reply_text('Введите количество денег:')
        return 1
    except Exception:
        update.message.reply_text('Не удалось обработать запрос', reply_markup=start_keyboard())
        print(traceback.format_exc())
    return ConversationHandler.END


def set_from_cur(update, context):
    try:
        cur = update.message['text']
        if cur in ' '.join(context.user_data['currencies']):
            context.user_data['from_cur'] = cur
            update.message.reply_text('Выберите валюты, в которую хотите перевести деньги:')
            return 3
        else:
            update.message.reply_text('Данной валюты нет в списке')
            update.message.reply_text('Выберите валюту, из который переводите деньги:')
            return 2
    except Exception:
        update.message.reply_text('Не удалось обработать запрос', reply_markup=start_keyboard())
        print(traceback.format_exc())
    clear_data(context)
    return ConversationHandler.END


def set_to_cur(update, context):
    try:
        cur = update.message['text']
        if cur in ' '.join([i.split()[0] for i in context.user_data['currencies']]):
            context.user_data['to_cur'] = cur
            amount = context.user_data['amount']
            from_cur = context.user_data['from_cur']
            url = "https://currency-exchange.p.rapidapi.com/exchange"
            params = {"to": cur, "from": from_cur}
            headers = {
                "X-RapidAPI-Host": "currency-exchange.p.rapidapi.com",
                "X-RapidAPI-Key": "5ba360e216mshff693a6a557ef28p19c45bjsne7791971c241"
            }
            response = requests.request("GET", url, headers=headers, params=params)
            update.message.reply_text(f'{float(response.text) * amount} {cur}', reply_markup=start_keyboard())
        else:
            update.message.reply_text('Данной валюты нет в списке')
            update.message.reply_text('Выберите валюты, в которую хотите перевести деньги:')
            return 3
    except Exception:
        update.message.reply_text('Не удалось обработать запрос', reply_markup=start_keyboard())
        print(traceback.format_exc())
    clear_data(context)
    return ConversationHandler.END


# Прогноз погоды
def forecast(update, context):
    try:
        dict_wind = {'nw': 'северо-западное', 'n': 'северное', 'ne': 'северо-восточное', 'e': 'восточное',
                     'se': 'юго-восточное', 's': 'южное', 'sw': 'юго-западное', 'w': 'западное', 'c': 'штиль'}
        place = update.message['text']
        if place.isdigit():
            update.message.reply_text('Некорректное название города')
            update.message.reply_text('Введите название города:')
            return 1
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
        ts = int(response['now'])
        date = datetime.utcfromtimestamp(ts).strftime('%d.%m.%Y')
        temp = response['fact']['temp']
        feels_temp = response['fact']['feels_like']
        condition = translate(response['fact']['condition'], 'en', 'ru')
        pressure = response['fact']['pressure_mm']
        humidity = response['fact']['humidity']
        wind_speed = response['fact']['wind_speed']
        wind_dir = dict_wind[response['fact']['wind_dir']]
        update.message.reply_text(f'Прогноз погоды сегодня в городе {place.capitalize()} на {date}:')
        update.message.reply_text(f'Температура: {temp}℃')
        update.message.reply_text(f'Ощущаемая температура: {feels_temp}℃')
        update.message.reply_text(f'Погодное описание: {condition.lower()}')
        update.message.reply_text(f'Давление: {pressure} мм')
        update.message.reply_text(f'Влажность: {humidity}%')
        update.message.reply_text(f'Скорость ветра: {wind_speed} м/с')
        update.message.reply_text(f'Направление ветра: {wind_dir}', reply_markup=start_keyboard())
    except Exception:
        update.message.reply_text('Не удалось обработать ваш запрос', reply_markup=start_keyboard())
    return ConversationHandler.END


# Переводчик
def set_from_lang(update, context):
    try:
        lang = update.message['text']
        if lang in context.user_data['languages'].keys():
            context.user_data['from_lang'] = lang
            update.message.reply_text('Выберите язык, на который хотите перевести текст:')
        else:
            update.message.reply_text('Данного языка нет в списке')
            update.message.reply_text('Выберите язык, с которого переводите текст:')
            return 1
        return 2
    except Exception:
        update.message.reply_text('Не удалось обработать ваш запрос', reply_markup=start_keyboard())
        clear_data(context)
        return ConversationHandler.END


def set_to_lang(update, context):
    try:
        lang = update.message['text']
        if lang in context.user_data['languages'].keys():
            context.user_data['to_lang'] = lang
            update.message.reply_text('Введите текст для перевода:', reply_markup=ReplyKeyboardRemove())
        else:
            update.message.reply_text('Данного языка нет в списке')
            update.message.reply_text('Выберите язык, на который хотите перевести текст:')
            return 2
        return 3
    except Exception:
        update.message.reply_text('Не удалось обработать ваш запрос', reply_markup=start_keyboard())
        clear_data(context)
        return ConversationHandler.END


def set_text_for_translate(update, context):
    try:
        text = update.message['text']
        from_lang = context.user_data['from_lang']
        to_lang = context.user_data['to_lang']
        languages = context.user_data['languages']
        update.message.reply_text(translate(text, languages[from_lang], languages[to_lang]),
                                  reply_markup=start_keyboard())
    except Exception:
        update.message.reply_text('Не удалось обработать ваш запрос', reply_markup=start_keyboard())
    clear_data(context)
    return ConversationHandler.END


# Проверка орфографии
def spell_checker(update, context):
    try:
        # text = re.sub(r'[^\w\s]', '', update.message['text']).split()
        text = update.message['text'].split()
        url_checker = 'https://speller.yandex.net/services/spellservice.json/checkText?'
        params = {'text': '+'.join(text)}
        response = requests.get(url_checker, params=params).json()
        if len(response) == 0:
            update.message.reply_text('Ошибок в тексте не обнаружено', reply_markup=start_keyboard())
        else:
            update.message.reply_text(f'Количество ошибок: {len(response)}')
            for i in response:
                incor, cor = i['word'], i['s'][0]
                update.message.reply_text(f'Неправильно: {incor}')
                update.message.reply_text(f'Правильно: {cor}')
            update.message.reply_text('Вывод ошибок окончен', reply_markup=start_keyboard())
    except Exception:
        update.message.reply_text('Не удалось обработать ваш запрос', reply_markup=start_keyboard())
    return ConversationHandler.END


# Проверка ip-адреса
def ip_checker(update, context):
    try:
        ip = update.message['text']
        if re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", ip):
            response = requests.get(f'http://ipwhois.app/json/{ip}').json()
            update.message.reply_text(f'Континент: {translate(response["continent"], "en", "ru")}')
            update.message.reply_text(f'Страна: {translate(response["country"], "en", "ru")}')
            update.message.reply_text(f'Регион: {translate(response["region"], "en", "ru")}')
            update.message.reply_text(f'Город: {translate(response["city"], "en", "ru")}')
            update.message.reply_text('Расположение IP-адреса на карте:', reply_markup=start_keyboard())
            lat, lon = response['latitude'], response['longitude']
            bot = Bot('5147228144:AAG-lIcg7-YZJqpJ5gfHZrR_J6hBtAZomO0')
            bot.send_location(update['message']['chat']['id'], lat, lon)
        else:
            update.message.reply_text('Некорректный IP-адрес')
            update.message.reply_text('Введите IP-адрес:')
            return 1
    except Exception:
        update.message.reply_text('Не удалось обработать ваш запрос', reply_markup=start_keyboard())
    return ConversationHandler.END


# Проверка номера телефона
def phone_number_checker(update, context):
    try:
        number = update.message['text']
        key = '658b78d8286245e6b363f9fe2bd632da'
        params = {'number': number, 'access_key': key}
        response = requests.get('http://apilayer.net/api/validate?', params=params).json()
        if (response.get('error')) or (response['valid'] is not True):
            update.message.reply_text('Введён неправильный формат для номера телефона')
            update.message.reply_text('Введите номер телефона:')
            return 1
        else:
            phone_number = response['number']
            country = response['country_name']
            location = response['location']
            carrier = response['carrier']
            update.message.reply_text(f'Информация по номеру {phone_number}:')
            update.message.reply_text(f'Страна: {translate(country, "en", "ru")}')
            update.message.reply_text(f'Местоположение: {translate(location, "en", "ru")}')
            update.message.reply_text(f'Оператор: {carrier}', reply_markup=start_keyboard())
    except Exception:
        print(traceback.format_exc())
        update.message.reply_text('Не удалось обработать ваш запрос', reply_markup=start_keyboard())
    return ConversationHandler.END


# Остановщик
def stop(update, context):
    clear_data(context)
    update.message.reply_text('Программа завершена', reply_markup=start_keyboard())
    return ConversationHandler.END


def main():
    token = '5147228144:AAG-lIcg7-YZJqpJ5gfHZrR_J6hBtAZomO0'
    updater = Updater(token)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start, pass_user_data=True))
    forecast_handler = ConversationHandler(
        entry_points=[CommandHandler('forecast', first_response)],
        states={
            1: [MessageHandler(Filters.text & (~ Filters.command), forecast)]
        },
        fallbacks=[CommandHandler('stop', stop, pass_user_data=True)]
    )
    dp.add_handler(forecast_handler)
    converter_handler = ConversationHandler(
        entry_points=[CommandHandler('converter_currency', first_response, pass_user_data=True)],
        states={
            1: [MessageHandler(Filters.text & (~ Filters.command), set_amount, pass_user_data=True)],
            2: [MessageHandler(Filters.text & (~ Filters.command), set_from_cur, pass_user_data=True)],
            3: [MessageHandler(Filters.text & (~ Filters.command), set_to_cur, pass_user_data=True)]
        },
        fallbacks=[CommandHandler('stop', stop, pass_user_data=True)]
    )
    dp.add_handler(converter_handler)
    translate_handler = ConversationHandler(
        entry_points=[CommandHandler('translate', first_response, pass_user_data=True)],
        states={
            1: [MessageHandler(Filters.text & (~ Filters.command), set_from_lang, pass_user_data=True)],
            2: [MessageHandler(Filters.text & (~ Filters.command), set_to_lang, pass_user_data=True)],
            3: [MessageHandler(Filters.text & (~ Filters.command), set_text_for_translate, pass_user_data=True)]
        },
        fallbacks=[CommandHandler('stop', stop, pass_user_data=True)]
    )
    dp.add_handler(translate_handler)
    spell_handler = ConversationHandler(
        entry_points=[CommandHandler('spell_check', first_response)],
        states={
            1: [MessageHandler(Filters.text & (~ Filters.command), spell_checker)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    dp.add_handler(spell_handler)
    ip_handler = ConversationHandler(
        entry_points=[CommandHandler('ip_check', first_response)],
        states={
            1: [MessageHandler(Filters.text & (~ Filters.command), ip_checker)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    dp.add_handler(ip_handler)
    phone_number_handler = ConversationHandler(
        entry_points=[CommandHandler('phone_number_check', first_response)],
        states={
            1: [MessageHandler(Filters.text & (~ Filters.command), phone_number_checker)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    dp.add_handler(phone_number_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
