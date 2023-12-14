# vim: ts=4 sw=4 et ai

import asyncio
import logging
from pysiptest.rtpplay import RtpPlay

async def play(pcap_name=None):
    loop = asyncio.get_running_loop()
    on_con_lost = loop.create_future()

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: RtpPlay(on_con_lost, 'sipp_call.pcap'),
        remote_addr=('127.0.0.1', 9999))
    protocol.begin()

    print(dir(transport))
    print(transport._sock.getsockname())
    try:
        #await on_con_lost
        pass
    finally:
        transport.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(play())
