from os import path

from quart_openapi import Pint

from service import config


app = Pint(__name__, title='Exact Time Service',
           no_openapi=True, validate=False,
           base_model_schema=path.join(path.dirname(__file__),
                                       'base_model_schema.json')
           )
app.config.from_object(config)


import service.view
