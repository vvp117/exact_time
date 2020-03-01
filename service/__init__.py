from os import environ, path

from quart_openapi import Pint

import service.config as default_config


app = Pint(__name__, title='Exact Time Service',
           no_openapi=True, validate=False,
           base_model_schema=path.join(path.dirname(__file__),
                                       'base_model_schema.json')
           )
app.config.from_object(default_config)


config_file = environ.get('QUART_CONFIG')
if config_file:
    app.config.from_pyfile(config_file)


import service.view
