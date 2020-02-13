from os import environ

from quart import Quart

import service.config as default_config


app = Quart(__name__)
app.config.from_object(default_config)


config_file = environ.get('QUART_CONFIG')
if config_file:
    app.config.from_pyfile(config_file)


import service.view
