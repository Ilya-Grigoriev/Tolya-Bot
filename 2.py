import datetime

unix_time = 1650304800
date_time = datetime.datetime.fromtimestamp(unix_time)
print(date_time.strftime('%Y-%m-%d %H:%M:%S'))
