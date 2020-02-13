DEBUG = False
TESTING = False

# Генерация: import os; print(os.urandom(16))
SECRET_KEY = 'dev-secret-key'

# Эта настройка требуется, чтобы получить
# тексты ошибок от сервера кириллицей без проблем.
# Иначе содержимое JSON будет закодировано в UTF-8
# при отображении
JSON_AS_ASCII = False

NTP_SERVER = '<ntp-server>'  # for example: 'ntp1.stratum1.ru'
NTP_PORT = 123
NTP_VERSION = 4  # 3 or 4, current - 4
