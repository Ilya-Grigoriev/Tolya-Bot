import requests
from datetime import datetime
import json


url = 'https://api.openweathermap.org/data/2.5/weather?'
params = {'q': 'Казань', 'appid': '8c8f1d5a14047d61ab958d3874d1d63c', 'lang': 'ru', 'units': 'metric'}
response = requests.get(url, params=params)
unix_time = response['dt']
date_time = datetime.fromtimestamp(unix_time)
date = date_time.strftime('%Y-%m-%d %H:%M:%S')
temp = response['main']['temp']
feels_temp = response['main']['feels_like']
condition = response['weather']['description']
pressure = response['main']['pressure']
humidity = response['main']['humidity']
wind_speed = response['wind']['speed']
clouds = response['clouds']['all']