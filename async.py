#!/usr/bin/env python3
# countasync.py

from asyncio import gather, create_task
import asyncio
import socket
import json
from lxml import etree as ET
import logging
import re

logger=logging.getLogger(__name__)

async def data_to_json(data, length):
    if len(data) == length:
        pass
    elif len(data)-2 == length:
        pass
    else:
        logger.error(f'Length do not match Data: {len(data)} Encoded: {length}')
    try:
        x = json.loads(data.decode('utf-8'))
    except json.JSONDecodeError:
        logger.error(f'Problem data: {data}')
        return None
    return x

async def read_data(loop, client):
    logger.setLevel(logging.INFO)
    if client is None:
        return
    header = await loop.sock_recv(client, 8)
    logger.debug(f'Header : b{header}')
    
    length = int.from_bytes(header, byteorder="little")
    logger.info(f'Length : {length}')
    if length == 0:
        return 
    request = b''
    length += 2 # CR LF on the end
    lengthRemaining = length 
    while lengthRemaining > 0:
        request += await loop.sock_recv(client, lengthRemaining) #.decode('utf8') # plus the CR LF on the end
        lengthRemaining = length - len(request)
        print(f'Remaining length {lengthRemaining} of {length}')
    logger.debug(f'Request : {request}')

    payload = await data_to_json(request, length)
    logger.debug(f'Payload : {payload}')
    return payload


async def write_data(loop, client, msg):
    data = len(msg).to_bytes(8, byteorder="little") + bytes(msg,"utf-8")
    await loop.sock_sendall(client, data)
    #loop.sock_
    #return data

async def getAllCricHQ(loop, client):
    commands = [
        '{"method": "getScorecard", "apiVersion": "1.1.2" }',
        '{"method": "getDuckworthLewisStern", "apiVersion": "1.1.2" }',
        '{"method": "getMatchScoreView", "apiVersion": "1.1.2" }',
        '{"method": "getBattingBowlingView", "apiVersion": "1.1.2" }',
        '{"method": "getTickerTape", "apiVersion": "1.1.2" }',
    ]
    tasks = [
        create_task(write_data(loop, client, commands[0])),
        create_task(write_data(loop, client, commands[1])),
        create_task(write_data(loop, client, commands[2])),
        create_task(write_data(loop, client, commands[3])),
        create_task(write_data(loop, client, commands[4])),
    ]
    await gather(*tasks)
    print('Now have all data to process the scorecard')
    return 'some stuff'

def vMix_setValue(vMix, name,value):
    vMixReader = vMix[0]
    vMixWriter = vMix[1]
    vMixXML = vMix[2]
    for element in vMixXML.xpath(f"//text[@name='{name}']"):
        vMixWriter.write(f'FUNCTION SetText Input={element.getparent().get("key")}&SelectedName={name}&Value={value}\r\n'.encode('utf-8'))
    return vMix

async def process_getScorecard(vMix, y):
    if len(y.get('inningsScorecards')) > 0:
        stats = y.get('inningsScorecards')[-1].get('stats')   
        vMix = vMix_setValue(vMix,'score',stats.get('score'))
        vMix = vMix_setValue(vMix,'overIndex',stats.get('overIndex'))
        vMix = vMix_setValue(vMix,'wicketCount',stats.get('wicketCount'))
        vMix = vMix_setValue(vMix,'extraPoints',stats.get('extraPoints'))
        vMix = vMix_setValue(vMix,'rpo',int(stats.get('rpo')))
        vMix = vMix_setValue(vMix,'extraPoints',y['inningsScorecards'][-1]['stats']['extraPoints'])
    else:
        vMix = vMix_setValue(vMix,'score', '0')
        vMix = vMix_setValue(vMix,'overIndex','0')
        vMix = vMix_setValue(vMix,'wicketCount','0')
        vMix = vMix_setValue(vMix,'extraPoints','0')
        vMix = vMix_setValue(vMix,'rpo','0')
        vMix = vMix_setValue(vMix,'firstInningsScore','0')
        vMix = vMix_setValue(vMix,'extraPoints','0')
    if y.get('inningsIndex',-1) > 0:
        # have a first Innings score
        vMix = vMix_setValue(vMix,'firstInningsScore',y['inningsScorecards'][0]['stats']['score'])
    else:
        vMix = vMix_setValue(vMix,'firstInningsScore','0')
    if y['isHomeTeamBatting']:
        vMix = vMix_setValue(vMix,'battingTeamName', re.split("\s|(?<!\d)[,.](?!\d)",y['homeTeamBasic']['name'])[0].upper()) # use regex to split space comma etc.
        vMix = vMix_setValue(vMix,'bowlingTeamName', re.split("\s|(?<!\d)[,.](?!\d)",y['awayTeamBasic']['name'])[0].upper())
    else:
        vMix = vMix_setValue(vMix,'bowlingTeamName', re.split("\s|(?<!\d)[,.](?!\d)",y['homeTeamBasic']['name'])[0].upper())
        vMix = vMix_setValue(vMix,'battingTeamName', re.split("\s|(?<!\d)[,.](?!\d)",y['awayTeamBasic']['name'])[0].upper())
    return vMix # So if we have reconnected or the XML state has been update





async def handle_client(client):
    loop = asyncio.get_event_loop()
    request = None
    data = ''
    vMix = await vMixClient()
    while request != 'quit' and client is not None:

        request = await read_data(loop, client)
        logger.debug(f'Log {request}')
        if request is not None:
            print(request.get('methodCaller'))
            if request.get('methodCaller') == 'getLastEvent':
                data = await getAllCricHQ(loop, client)
            elif request.get('methodCaller') == 'getScorecard':
                await process_getScorecard(vMix, request)
        else:
            print('Request was a None so I think Close the client')
            if client is not None: client.close()
        
        #response = str(eval(request)) + '\n'
        #await loop.sock_sendall(client, response.encode('utf8'))
    if client is not None: client.close()

async def run_cricHQ_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((socket.gethostname(), 9090))
    server.listen(8)
    server.setblocking(False)
    loop = asyncio.get_event_loop()
    vMixQ = asyncio.Queue()
    while True:
        
        client, _ = await loop.sock_accept(server)
        loop.create_task(handle_client(client))


async def vMixClient(ip='127.0.0.1', port=8099):
    reader, writer = await asyncio.open_connection(
        ip, port)
    print('Opening vMix')
    vMixXML = await get_vMixXML(reader, writer)
    return (reader, writer, vMixXML)

async def get_vMixXML(reader, writer):
    writer.write('XML\r\n'.encode('utf-8'))
    while True:
        response = (await reader.readuntil('\r\n'.encode('utf-8'))).decode('utf-8')
        if response.startswith('XML'):
            break
    logger.info(f'Get XML {response}')
    _, _, slength = response.partition(' ')
    length = int(slength)
    rawXML = (await reader.readexactly(length))
    logger.info(f'GetXML reported length {length} actual length {len(rawXML)}')
    xml = ET.fromstring(rawXML.decode('utf-8'))
    return xml

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    asyncio.run(run_cricHQ_server())
