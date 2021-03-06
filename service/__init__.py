from os import environ

from quart_openapi import Pint

import service.config as default_config


app = Pint(__name__, no_openapi=True, title='Exact Time Service')
app.config.from_object(default_config)


config_file = environ.get('QUART_CONFIG')
if config_file:
    app.config.from_pyfile(config_file)


import service.view
