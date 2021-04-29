#!/usr/bin/env python3
# countasync.py

from asyncio import gather, create_task
import asyncio
import socket
import json
from lxml import etree as ET
import logging
import re

ACTIVE_SYM = '*'
INACTIVE_SYM = ' '

wicketType = {
    0   : 'Not out',
    1   : 'Bowled',
    2   : 'Caught',
    3   : 'LBW',
    4   : 'Stumped',
    5   : 'Run Out',
    6   : 'Hit Wicket',
    7   : 'Handled Ball',
    8   : 'Hit Twice',
    9   : 'Timeout',
    10  : 'Obstructing',
}

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

async def read_data(loop, reader, writer):
    logger.setLevel(logging.INFO)
    # if client is None:
    #     return
    try:
        header = await reader.readexactly(8)
    except asyncio.exceptions.IncompleteReadError:
        return 'quit'
    logger.debug(f'Header : b{header}')
    
    length = int.from_bytes(header, byteorder="little")
    logger.info(f'Length : {length}')
    if length == 0:
        return 
    request = b''
    length += 2 # CR LF on the end
    lengthRemaining = length 
    while lengthRemaining > 0:
        request += await reader.readexactly(length) #.decode('utf8') # plus the CR LF on the end
        lengthRemaining = length - len(request)
        print(f'Remaining length {lengthRemaining} of {length}')
    logger.debug(f'Request : {request}')

    payload = await data_to_json(request, length)
    logger.debug(f'Payload : {payload}')
    return payload

def write_data(loop, reader, writer,  msg):
    data = len(msg).to_bytes(8, byteorder="little") + bytes(msg,"utf-8")
    writer.write(data)

async def getAllCricHQ(loop, reader, writer):
    commands = [
        '{"method": "getScorecard", "apiVersion": "1.1.2" }',
        '{"method": "getDuckworthLewisStern", "apiVersion": "1.1.2" }',
        '{"method": "getMatchScoreView", "apiVersion": "1.1.2" }',
        '{"method": "getBattingBowlingView", "apiVersion": "1.1.2" }',
        '{"method": "getTickerTape", "apiVersion": "1.1.2" }',
    ]
    for command in commands:
        write_data(loop, reader, writer, command)
    return

async def vMix_setValue(vMix, name,value):
    if vMix is None:
        vMix = await vMixClient()
    vMixReader = vMix[0]
    vMixWriter = vMix[1]
    vMixXML = vMix[2]
    for element in vMixXML.xpath(f"//text[@name='{name}']"):
        vMixWriter.write(f'FUNCTION SetText Input={element.getparent().get("key")}&SelectedName={name}&Value={value}\r\n'.encode('utf-8'))
    return vMix

async def writeDumpFile(data, fileName):
    with open(fileName,'w') as f:
        f.write(json.dumps(data, indent=4, sort_keys=True))
    
    return

async def process_getScorecard(vMix, y):
    logger.info(f'getScorecard :{y}')
    await writeDumpFile(y, 'getScorecard.json')
    if len(y.get('inningsScorecards')) > 0:
        stats = y.get('inningsScorecards')[-1].get('stats')   
        vMix = await vMix_setValue(vMix,'score',stats.get('score'))
        vMix = await vMix_setValue(vMix,'overIndex',stats.get('overIndex'))
        vMix = await vMix_setValue(vMix,'wicketCount',stats.get('wicketCount'))
        vMix = await vMix_setValue(vMix,'extraPoints',stats.get('extraPoints'))
        vMix = await vMix_setValue(vMix,'rpo',int(stats.get('rpo')))
        # stats['wicketCount']
        outOver = 0
        lastBatter = None
        try:
            for batter in y.get('inningsScorecards')[y['inningsIndex']].get('batterListStats'):
                if batter['isDismissed']:
                    if batter['outAction']['overIndex'] >= outOver:  # gt or eq so hopefully two wickets in the same over work out right..??
                        outOver = batter['outAction']['overIndex']
                        lastBatter = batter
                    print(batter['outAction']['overIndex'])
                    print(batter['outAction']['wicketType'])
        except IndexError as e:
            logger.info(f'IndexError {e} - probably end of innings')
        if lastBatter is None:
            lastWkt = ''
        else:
            howOut = wicketType[lastBatter['outAction']['wicketType']]
            who = lastBatter['batter']['name'].split(' ')[-1]
            lastWkt = who + '\r\n' + howOut
        vMix = await vMix_setValue(vMix,'lastWkt', lastWkt)
    else:
        vMix = await vMix_setValue(vMix,'score', '0')
        vMix = await vMix_setValue(vMix,'overIndex','0')
        vMix = await vMix_setValue(vMix,'wicketCount','0')
        vMix = await vMix_setValue(vMix,'extraPoints','0')
        vMix = await vMix_setValue(vMix,'rpo','0')
        vMix = await vMix_setValue(vMix,'firstInningsScore','0')
        vMix = await vMix_setValue(vMix,'extraPoints','0')
        vMix = await vMix_setValue(vMix,'lastWkt','')
    if y.get('inningsIndex',-1) > 0:
        # have a first Innings score
        vMix = await vMix_setValue(vMix,'firstInningsScore',y['inningsScorecards'][0]['stats']['score'])
    else:
        vMix = await vMix_setValue(vMix,'firstInningsScore','0')
    if y['isHomeTeamBatting']:
        vMix = await vMix_setValue(vMix,'battingTeamName', re.split("\s|(?<!\d)[,.](?!\d)",y['homeTeamBasic']['name'])[0].upper()) # use regex to split space comma etc.
        vMix = await vMix_setValue(vMix,'bowlingTeamName', re.split("\s|(?<!\d)[,.](?!\d)",y['awayTeamBasic']['name'])[0].upper())
    else:
        vMix = await vMix_setValue(vMix,'bowlingTeamName', re.split("\s|(?<!\d)[,.](?!\d)",y['homeTeamBasic']['name'])[0].upper())
        vMix = await vMix_setValue(vMix,'battingTeamName', re.split("\s|(?<!\d)[,.](?!\d)",y['awayTeamBasic']['name'])[0].upper())
    return vMix # So if we have reconnected or the XML state has been update

async def process_getDuckworthLewisStern(vMix, y):
    logger.info(f'getDuckworthLewisStern :{y}')
    await writeDumpFile(y, 'getDuckworthLewisStern.json')
    vMix = await vMix_setValue(vMix,'oversRemaining',int(y['oversRemainingIncludingBreaks']))
    vMix = await vMix_setValue(vMix,'dlsParScore',y['parScore'])
    return vMix

async def process_getMatchScoreView(vMix, y):
    logger.info(f'getMatchScoreView :{y}')
    await writeDumpFile(y, 'getMatchScoreView.json')
    return vMix

async def process_getBattingBowlingView(vMix, y):
    logger.info(f'getBattingBowlingView :{y}')
    await writeDumpFile(y, 'getBattingBowlingView.json')
    # get we have enough data in y...
    if y.get('facingBatsmanStats','') == '' or y.get('nonFacingBatsmanStats','') == '':
        return vMix
    if y['facingBatsmanStats']['batterOrderIndex'] < y['nonFacingBatsmanStats']['batterOrderIndex']:
        faceing = 1
        nonFaceing = 2
    else:
        faceing = 2
        nonFaceing = 1
    vMix = await vMix_setValue(vMix,f'batterName{faceing}',y['facingBatsmanStats']['batter']['name'].split(' ')[-1].upper())
    vMix = await vMix_setValue(vMix,f'batterScore{faceing}',y['facingBatsmanStats']['score'])
    vMix = await vMix_setValue(vMix,f'batterActive{faceing}',ACTIVE_SYM)
    
    vMix = await vMix_setValue(vMix,f'batterName{nonFaceing}',y['nonFacingBatsmanStats']['batter']['name'].split(' ')[-1].upper())
    vMix = await vMix_setValue(vMix,f'batterScore{nonFaceing}',y['nonFacingBatsmanStats']['score'])
    vMix = await vMix_setValue(vMix,f'batterActive{nonFaceing}',INACTIVE_SYM)
    if y.get('bowlerStats','') == '': 
        vMix = await vMix_setValue(vMix,f'bowlerName1','')
        vMix = await vMix_setValue(vMix,f'bowlerActive1', INACTIVE_SYM)        
    if y.get('nonActiveBowlerStats','') == '':
        if y.get('bowlerStats','') != '':
            vMix = await vMix_setValue(vMix,f'bowlerName1',y['bowlerStats']['bowler']['name'].split(' ')[-1].upper())
        vMix = await vMix_setValue(vMix,f'bowlerActive1', ACTIVE_SYM)
        vMix = await vMix_setValue(vMix,f'bowlerName2','')
        vMix = await vMix_setValue(vMix,f'bowlerActive2', INACTIVE_SYM)
    else:
        if y.get('bowlerStats') is None:
            logger.info(f'getBattingBowlingView : data has no bowlerStats')
        else:
            if y['bowlerStats']['bowler']['id'] < y['nonActiveBowlerStats']['bowler']['id']:
                active = 1
                nonactive = 2
            else:
                active = 2
                nonactive = 1
            vMix = await vMix_setValue(vMix,f'bowlerName{active}',y['bowlerStats']['bowler']['name'].split(' ')[-1].upper())
            vMix = await vMix_setValue(vMix,f'bowlerActive{active}', ACTIVE_SYM)
            vMix = await vMix_setValue(vMix,f'bowlerName{nonactive}',y['nonActiveBowlerStats']['bowler']['name'].split(' ')[-1].upper())
            vMix = await vMix_setValue(vMix,f'bowlerActive{nonactive}', INACTIVE_SYM)    
    return vMix

async def process_getTickerTape(vMix, y):
    logger.info(f'getTickerTape :{y}')
    await writeDumpFile(y, 'getTickerTape.json')
    return vMix

async def handle_client(reader, writer):
    loop = asyncio.get_event_loop()
    request = None
    vMix = await vMixClient()
    while request != 'quit':
        logger.debug(f'Request: {request}')
        if request is not None:
            methodCaller = request.get('methodCaller')
            logger.info(f'methodCaller: {methodCaller}')
            if methodCaller == 'getLastEvent':
                data = await getAllCricHQ(loop, reader, writer)
            elif methodCaller == 'getScorecard':
                await process_getScorecard(vMix, request)            
            elif methodCaller == 'getDuckworthLewisStern':
                await process_getDuckworthLewisStern(vMix, request)
            elif methodCaller == 'getMatchScoreView':
                await process_getMatchScoreView(vMix, request)
            elif methodCaller == 'getBattingBowlingView':
                await process_getBattingBowlingView(vMix, request)
            elif methodCaller == 'getTickerTape':
                await process_getTickerTape(vMix, request)                
        request = await read_data(loop, reader, writer)
        if vMix is None: vMix = await vMixClient()
    logger.info(f'Closing connection from ?')
    writer.close()    

async def run_cricHQ_server():
    server = await asyncio.start_server(handle_client, socket.gethostname(), 9090)
    async with server:
        await server.serve_forever()

async def vMixClient(ip='127.0.0.1', port=8099):
    logger.info(f'Connecting to vMix {ip}:{port}')
    try:
        reader, writer = await asyncio.open_connection(
            ip, port)
    except ConnectionRefusedError:
        logger.error(f'Unable to connect to vMix {ip}:{port}')
        reader = writer = vMixXML = None
    if writer is not None: 
        vMixXML = await get_vMixXML(reader, writer)
        return (reader, writer, vMixXML)
    return None

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
