from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot
import requests
from datetime import datetime
import traceback
import re
import xml.etree.ElementTree as ET


def clear_data(context):
    context.user_data['amount'] = None
    context.user_data['from_cur'] = None
    context.user_data['to_cur'] = None
    context.user_data['from_lang'] = None
    context.user_data['to_lang'] = None
    context.user_data['songs'] = None


def start_keyboard():
    reply_keyboard = [['Прогноз погоды', 'Конвертер валют', 'Переводчик текста'], ['Орфографический анализ текста'],
                      ['Получение информации по IP-адресу', 'Получение информации по номеру телефона'],
                      ['Сократитель ссылок', 'Поиск текста песни', 'Случайный анекдот']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    return markup


def first_response(update, context):
    context.user_data['languages'] = {'Французский': 'fr', 'Испанский': 'es', 'Русский': 'ru', 'Арабский': 'ar',
                                      'Португальский': 'pt', 'Немецкий': 'de', 'Английский': 'en', 'Китайский': 'zh'}
    if update.message['text'] == 'Прогноз погоды':
        update.message.reply_text('Введите название города:')
        return 'FORECAST'
    elif update.message['text'] == 'Конвертер валют':
        update.message.reply_text('Введите количество денег:')
        return 'SET_AMOUNT'
    elif update.message['text'] == 'Переводчик текста':
        reply_keyboard = [[i] for i in context.user_data['languages']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        update.message.reply_text('Выберите язык, с которого переводите текст:', reply_markup=markup)
        return 'SET_FROM_LANG'
    elif update.message['text'] == 'Орфографический анализ текста':
        update.message.reply_text('Введите текст для проверки:')
        return 'SPELL_CHECK'
    elif update.message['text'] == 'Получение информации по IP-адресу':
        update.message.reply_text('Введите IP-адрес:')
        return 'IP_CHECK'
    elif update.message['text'] == 'Получение информации по номеру телефона':
        update.message.reply_text('Введите номер телефона:')
        return 'PHONE_NUMBER_CHECK'
    elif update.message['text'] == 'Сократитель ссылок':
        update.message.reply_text('Введите ссылку:')
        return 'URL_SHORTENER'
    elif update.message['text'] == 'Поиск текста песни':
        update.message.reply_text('Введите имя испольнителя:')
        return 'SET_SINGER'
    elif update.message['text'] == 'Случайный анекдот':
        update.message.reply_text('Внимание! В анекдоте может присутствовать нецензурная брань')
        for i in anecdote():
            update.message.reply_text(i)
        update.message.reply_text('Конец анекдота!', reply_markup=start_keyboard())
    return ConversationHandler.END


def start(update, context):
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
    with open('currencies.txt', encoding='utf8') as file_1:
        context.user_data['currencies'] = [i.strip('\n') for i in file_1.readlines()]
    try:
        context.user_data['amount'] = float(update.message['text'])
        if context.user_data['amount'] < 0:
            update.message.reply_text('Нельзя вводить отрицательное количество денег')
            update.message.reply_text('Введите количество денег:')
            return 'SET_AMOUNT'
        update.message.reply_text('\n'.join(context.user_data['currencies']))
        reply_keyboard = [[i.split()[0]] for i in context.user_data['currencies']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        update.message.reply_text('Выберите валюту, из который переводите деньги:', reply_markup=markup)
        return 'SET_FROM_CUR'
    except ValueError:
        update.message.reply_text('Введите количество денег:')
        return 'SET_AMOUNT'
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
            return 'SET_TO_CUR'
        else:
            update.message.reply_text('Данной валюты нет в списке')
            update.message.reply_text('Выберите валюту, из который переводите деньги:')
            return 'SET_FROM_CUR'
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
            return 'SET_TO_CUR'
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
            return 'FORECAST'
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
            raise Exception
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
            return 'SET_FROM_LANG'
        return 'SET_TO_LANG'
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
            return 'SET_TO_LANG'
        return 'SET_TEXT_FOR_TRANSLATE'
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
            return 'IP_CHECK'
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
            return 'PHONE_NUMBER_CHECK'
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


# Сокращение URL-адресов
def url_shortener(update, context):
    try:
        link = update.message['text']
        url = "https://url-shortener-service.p.rapidapi.com/shorten"
        payload = f"url={link}"
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "X-RapidAPI-Host": "url-shortener-service.p.rapidapi.com",
            "X-RapidAPI-Key": "5ba360e216mshff693a6a557ef28p19c45bjsne7791971c241"
        }
        response = requests.request("POST", url, data=payload, headers=headers).json()
        if response.get('error'):
            update.message.reply_text('Введена некорректная ссылка')
            update.message.reply_text('Введите ссылку:')
            return 'URL_SHORTENER'
        else:
            update.message.reply_text('Итоговый вид сокращённой ссылки:')
            update.message.reply_text(response['result_url'], reply_markup=start_keyboard())
    except Exception:
        print(traceback.format_exc())
        update.message.reply_text('Не удалось обработать ваш запрос', reply_markup=start_keyboard())
    return ConversationHandler.END


# Получение текста песни
def set_singer(update, context):
    try:
        singer_name = update.message['text']
        url = "https://genius.p.rapidapi.com/search"
        querystring = {"q": singer_name}
        headers = {
            "X-RapidAPI-Host": "genius.p.rapidapi.com",
            "X-RapidAPI-Key": "5ba360e216mshff693a6a557ef28p19c45bjsne7791971c241"
        }
        response = requests.request("GET", url, headers=headers, params=querystring).json()
        songs = response['response']['hits']
        if len(songs) == 0:
            update.message.reply_text('Не удалось найти исполнителя')
            update.message.reply_text('Введите имя исполнителя:')
            return 'SET_SINGER'
        context.user_data['songs'] = songs
        update.message.reply_text('Введите название песни:')
        return 'SET_SONG'
    except Exception:
        update.message.reply_text('Не удалось обработать ваш запрос', reply_markup=start_keyboard())
    clear_data(context)
    return ConversationHandler.END


def set_song(update, context):
    try:
        song_name = update.message['text']
        songs = context.user_data['songs']
        id_song = None
        for i in songs:
            if song_name.lower() in i['result']['title'].lower():
                id_song = i['result']['api_path']
                break
        if bool(id_song) is not True:
            update.message.reply_text('Не удалось найти песню с таким названием')
            update.message.reply_text('Введите название песни:')
            return 'SET_SONG'
        url = f"https://genius-song-lyrics1.p.rapidapi.com/{id_song}/lyrics"
        headers = {
            "X-RapidAPI-Host": "genius-song-lyrics1.p.rapidapi.com",
            "X-RapidAPI-Key": "5ba360e216mshff693a6a557ef28p19c45bjsne7791971c241"
        }
        response = requests.request("GET", url, headers=headers).json()
        song = response['response']['lyrics']
        update.message.reply_text('Текст песни:')
        update.message.reply_text(song['lyrics']['body']['plain'],
                                  reply_markup=start_keyboard())
    except Exception:
        print(traceback.format_exc())
        update.message.reply_text('Не удалось обработать ваш запрос', reply_markup=start_keyboard())
    clear_data(context)
    return ConversationHandler.END


# Анекдот
def anecdote():
    try:
        text = update.message['text']
        response = requests.get('http://rzhunemogu.ru/Rand.aspx?CType=1')
        root = ET.fromstring(response.content.decode(response.encoding))
        list_1 = []
        for i in root:
            list_1.append(i.text)
        return list_1
    except Exception:
        print(traceback.format_exc())
        return ['Не удалось обработать ваш запрос']


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
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.text & (~ Filters.command), first_response)],
        states={
            'FORECAST': [MessageHandler(Filters.text & (~ Filters.command), forecast)],
            'SET_AMOUNT': [MessageHandler(Filters.text & (~ Filters.command), set_amount, pass_user_data=True)],
            'SET_FROM_CUR': [MessageHandler(Filters.text & (~ Filters.command), set_from_cur, pass_user_data=True)],
            'SET_TO_CUR': [MessageHandler(Filters.text & (~ Filters.command), set_to_cur, pass_user_data=True)],
            'SET_FROM_LANG': [MessageHandler(Filters.text & (~ Filters.command), set_from_lang, pass_user_data=True)],
            'SET_TO_LANG': [MessageHandler(Filters.text & (~ Filters.command), set_to_lang, pass_user_data=True)],
            'SET_TEXT_FOR_TRANSLATE': [
                MessageHandler(Filters.text & (~ Filters.command), set_text_for_translate, pass_user_data=True)],
            'SPELL_CHECK': [MessageHandler(Filters.text & (~ Filters.command), spell_checker)],
            'IP_CHECK': [MessageHandler(Filters.text & (~ Filters.command), ip_checker)],
            'PHONE_NUMBER_CHECK': [MessageHandler(Filters.text & (~ Filters.command), phone_number_checker)],
            'URL_SHORTENER': [MessageHandler(Filters.text & (~ Filters.command), url_shortener)],
            'SET_SINGER': [MessageHandler(Filters.text & (~ Filters.command), set_singer, pass_user_data=True)],
            'SET_SONG': [MessageHandler(Filters.text & (~ Filters.command), set_song, pass_user_data=True)],
        },
        fallbacks=[CommandHandler('stop', stop, pass_user_data=True)]
    )
    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()