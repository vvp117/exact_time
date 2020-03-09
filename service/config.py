DEBUG = False
TESTING = False

# Генерация: import os; print(os.urandom(16))
SECRET_KEY = ''

# Эта настройка требуется, чтобы получить
# тексты ошибок от сервера кириллицей без проблем.
# Иначе содержимое JSON будет закодировано в UTF-8
# при отображении
JSON_AS_ASCII = False

NTP_SERVER = ''  # for example: 'ntp1.stratum1.ru'
NTP_PORT = 123
NTP_VERSION = 4  # 3 or 4, current - 4


# Функция для переопределения значений этого
# файла конфигурации из переданных переменных среды
def override_from_env_vars():
    from os import environ
    from sys import modules

    #  Overriding configuration file values
    def booler(var):
        return True if var.lower() == 'true' else False

    converters = {
        'DEBUG': booler,
        'TESTING': booler,
        'NTP_PORT': int,
        'NTP_VERSION': int,
    }

    thismodule = modules[__name__]

    for var_name in dir(thismodule):
        if not var_name.isupper():
            continue

        env_var = environ.get(var_name)

        if env_var:
            converter = converters.get(var_name, str)
            setattr(thismodule, var_name, converter(env_var))


override_from_env_vars()
