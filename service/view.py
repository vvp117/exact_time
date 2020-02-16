from time import time, strftime, localtime
from functools import wraps

from quart import jsonify
from quart_openapi import Resource
import asyncio_dgram  # https://pypi.org/project/asyncio-dgram/
import ntplib as ntp  # https://pypi.org/project/ntplib/

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
    async def exact_time():
        host = app.config['NTP_SERVER']
        port = app.config['NTP_PORT']

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

    @params_to_doc(app.config['NTP_SERVER'])
    async def get(self):
        '''
        Returns exact time

        NTP Server used: {0}
        '''
        result = await ExactTimeService.exact_time()

        return jsonify(result)


@app.route('/api/v1/time/ya/suggest-geo/<string:name_part>', methods=['GET'])
@app.route('/api/v1/time/ya/sync/<int:geo_id>', methods=['GET'])
@app.route('/api/v1/time/ya/sync/by_list', methods=['POST'])
class YandexTimeService(Resource):

    @app.param('name_part',
               description='Part of the city name',
               _in='path', required=True)
    @app.param('geo_id',
               description='Yandex Geo-ID from */api/v1/time/ya/suggest-geo',
               _in='path', required=True)
    async def get(self, name_part='', geo_id=''):
        # https://suggest-maps.yandex.ru/suggest-geo?...
        # https://yandex.com/time/sync.json?geo=N

        result = {
            'host': 'yandex',
            'full_time': strftime('%Y.%m.%d %H:%M:%S %z', localtime()),
        }

        return jsonify(result)

    async def post(self):
        # https://yandex.com/time/sync.json?geo=65

        return jsonify({'relult': 'OK'})
