from time import time, strftime, localtime
from functools import wraps
from string import Template
from tempfile import gettempdir
from json import dumps

from quart import jsonify, abort, request
from quart_openapi import Resource
from quart_openapi.resource import get_expect_args
import asyncio_dgram  # https://pypi.org/project/asyncio-dgram/
import ntplib as ntp  # https://pypi.org/project/ntplib/
from aiohttp import ClientSession
from swagger_ui import api_doc

from service import app


@app.route('/openapi.json')
async def openapi():
    return jsonify(app.__schema__)


def params_to_doc(*params):

    def formatter(func):
        func.__doc__ = func.__doc__.format(*params)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    return formatter


@app.route('/api/v1/time/ntp', methods=['GET'])
class ExactTimeService(Resource):

    @staticmethod
    def create_ntp_request_data():
        ntp_query_packet = ntp.NTPPacket(
            mode=3,  # 3 = client, 4 = server
            version=app.config['NTP_VERSION'],
            tx_timestamp=ntp.system_to_ntp_time(time())
        )

        return ntp_query_packet.to_data()

    @staticmethod
    def get_ntp_stats(ntp_response_data):
        ntp_stats = ntp.NTPStats()

        ntp_stats.from_data(ntp_response_data)
        ntp_stats.dest_timestamp = ntp.system_to_ntp_time(time())

        return ntp_stats

    @staticmethod
    async def exact_time(host, port):
        host = host or app.config['NTP_SERVER']
        port = port or app.config['NTP_PORT']

        stream = await asyncio_dgram.connect((host, port))

        ntp_request = ExactTimeService.create_ntp_request_data()

        await stream.send(ntp_request)
        response_data, remote_addr = await stream.recv()

        stream.close()

        ntp_stats = ExactTimeService.get_ntp_stats(response_data)

        struct_time = localtime(ntp_stats.tx_time)

        result = {
            'host': host,
            'offset': ntp_stats.offset,
            'date': strftime('%Y.%m.%d', struct_time),
            'time': strftime('%H:%M:%S', struct_time),
            'zone': strftime('%z', struct_time),
            'full_time': strftime('%Y.%m.%d %H:%M:%S %z', struct_time),
            'ref_id': ntp.ref_id_to_text(ntp_stats.ref_id),
        }

        return result

    @app.param('ntp_server',
               description='Selected NTP-server',
               _in='query', required=False)
    @app.param('ntp_port',
               description='Port NTP-server (default: 123)',
               schema={'type': 'integer'},
               _in='query', required=False)
    @params_to_doc(app.config['NTP_SERVER'])
    async def get(self):
        '''
        Returns exact time

        Default NTP-server:port used: {0}:123
        '''
        ntp_server = request.args.get('ntp_server')
        ntp_port = int(request.args.get('ntp_port', 0))

        result = await ExactTimeService.exact_time(ntp_server, ntp_port)

        return jsonify(result)


@app.route('/api/v1/ya/suggest-geo/<string:name_part>')
class YandexSuggestGeo(Resource):
    SUGGEST_RESULTS = 10
    SUGGEST_VERSION = '9'

    url_template = Template(
        'https://suggest-maps.yandex.ru/suggest-geo'
        '?search_type=tune'
        f'&v={SUGGEST_VERSION}'
        f'&results={SUGGEST_RESULTS}'
        '&lang=ru_RU'
        '&part=$name_part'
    )

    @app.param('name_part',
               description='Part of the city name',
               _in='path', required=True)
    @params_to_doc(SUGGEST_RESULTS)
    async def get(self, name_part):
        '''
        Search for cities by name part

        Number of Results: {0}
        '''
        url = YandexSuggestGeo.url_template.substitute(
            name_part=name_part)

        result = None
        async with ClientSession() as session:
            async with session.get(url) as resp:
                result = await resp.json()

        return jsonify(result)


def validate_body(method):

    doc_attr = '__apidoc__'

    if not hasattr(method, doc_attr):
        raise KeyError(
            f'"{doc_attr}" attribute required! '
            'Place @validate_body higher than @app.expect')

    @wraps(method)
    async def wrapper(self, **kwargs):
        if request.headers.get('Content-Type') != 'application/json':
            raise abort(400,
                        description='Content type must be '
                        '"application / json"',
                        name='InvalidHeaders')

        for expect in getattr(method, doc_attr).get('expect', []):
            validator, content_type, _ = get_expect_args(expect)
            if content_type == 'application/json' and request.is_json:
                data = await request.get_json(force=True, cache=True)
                validator.validate(data)

        return await method(self, **kwargs)

    return wrapper


@app.route('/api/v1/ya/time')
class YandexTime(Resource):

    url_template = Template('https://yandex.com/time/sync.json?geo=$geo_ids')

    _, schema = app.base_model.resolve('#/components/schemas/ListGeoIDs')
    validator = app.create_validator('ya_time_request', schema)

    @validate_body
    @app.param('Content-Type',
               description='Need set "Content-Type": "application/json"',
               _in='header')
    @app.expect(validator, validate=False)
    async def post(self):
        '''
        Return time from Yandex

        Takes a geo-id array from \'*/api/v1/time/ya/suggest-geo\'
        '''
        geo_ids = await request.get_json()

        if not geo_ids:
            return abort(400,
                         description='Need parameters: array "geo_id"',
                         name='NoRequestParameters')

        geo_ids = [str(geo_id) for geo_id in geo_ids]
        url = YandexTime.url_template.substitute(
            geo_ids='&geo='.join(geo_ids)
        )

        async with ClientSession() as session:
            async with session.get(url) as resp:
                result = await resp.json()

        if not result:
            error_description = f'No data for this identifier ({geo_ids})'
            return abort(400, description=error_description)

        return jsonify(result)


@app.before_serving
async def add_swagger():
    swagger_config = f'{gettempdir()}/swagger.json'

    with open(swagger_config, 'w') as f:
        f.write(dumps(app.__schema__))

    api_doc(app, config_path=swagger_config,
            url_prefix='/api', title='API doc')
