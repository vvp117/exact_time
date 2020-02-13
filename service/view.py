from time import time, strftime, localtime

from quart import jsonify
from quart.views import MethodView
import asyncio_dgram  # https://pypi.org/project/asyncio-dgram/
import ntplib as ntp  # https://pypi.org/project/ntplib/

from service import app


class TimeService(MethodView):

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

        ntp_request = TimeService.create_ntp_request_data()

        await stream.send(ntp_request)
        response_data, remote_addr = await stream.recv()

        stream.close()

        ntp_stats = TimeService.get_ntp_stats(response_data)

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

    @app.route('/time')
    async def get():
        result = await TimeService.exact_time()

        return jsonify(result)
