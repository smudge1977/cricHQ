#! /usr/bin/env python3
'''
Title:         CricHQ.py
Description:   Interface with CricHQ Apple app API to update vMIX title graphics
Author:        Keith Marston
Version:       1.0
Last Update:   10/10/20

Look for #* to find things to enhance!

Dependancies:
    This uses my vMIX.py module which handles the vMix 8099 API interactions

    You need to register the server machine in mDNS with the following command:
    dns-sd -R scoreboard _cricviewing._tcp. local 9090 localhost 127.0.0.1

    This then allows the iPhone / iPad device to find the 'scorboard' i.e. the server we are running.
'''

import socket
import time
import logging
import logging.config
import struct 
import re
#from dataclasses import dataclass
import json
#from queue import Queue, Empty
#from threading import Thread, Event
#from time import sleep

import yaml

from vMix import VMix

def send_msg2(sock, msg):
    data = len(msg).to_bytes(8, byteorder="little") + bytes(msg,"utf-8")
    try:
        logger.debug(f'Sending {data}')
        sock.sendall(data)
    except:
        logger.error(f'Socket send error')   
    #return ((len(req)).to_bytes(8, byteorder="little") + bytes(req,"utf-8"))

def recv_msg2(sock):
    full_msg = ''
    new_msg = True
    finshed = False
    while not finshed:
        try:
            msg = sock.recv(1024)
        except ConnectionAbortedError:
            logger.info('CricHQ - Connection Aborted')
            break
        if new_msg:
            logger.info(f"New header : {msg[:HEADERSIZE]}")
            msglen = int.from_bytes(msg[:HEADERSIZE], byteorder="little")
            logger.debug(f'Message length {msglen}')
            new_msg = False
            msg = msg[HEADERSIZE:]
            logger.debug(f'Msg with out header {msg} is lenght {len(msg)}')
        logger.debug(f'full_msg length is {len(full_msg)} and the msglen is {msglen}')
        full_msg += msg.decode('utf-8')
        logger.debug(f'full_msg is now {len(full_msg)}')
        #- HEADERSIZE
        if len(full_msg) >= msglen:
            logger.info(f'Full msg len{len(full_msg)} and packet said {msglen} Message is : {full_msg}')
            finshed = True
    return full_msg

def computegetScoreCard(scorecardstr):
    if scorecardstr == "":
        logger.error('No scorecard passed')
    else:
        y = json.loads(scorecardstr)
        if y.get('methodCaller') == 'getScorecard':
            logger.info(f'CricHQ.Scores1.computegetScorecard : getscorecard : {str(scorecardstr)}')
            stats = y.get('inningsScorecards')[-1].get('stats')
            vMix.setValue('score',stats.get('score'))
            vMix.setValue('overIndex',stats.get('overIndex'))
            vMix.setValue('wicketCount',stats.get('wicketCount'))
            vMix.setValue('extraPoints',stats.get('extraPoints'))
            vMix.setValue('rpo',int(stats.get('rpo')))
            if y['isHomeTeamBatting']:
                vMix.setValue('battingTeamName', re.split("\s|(?<!\d)[,.](?!\d)",y['homeTeamBasic']['name'])[0].upper()) # use regex to split space comma etc.
                vMix.setValue('bowlingTeamName', re.split("\s|(?<!\d)[,.](?!\d)",y['awayTeamBasic']['name'])[0].upper())
            else:
                vMix.setValue('bowlingTeamName', re.split("\s|(?<!\d)[,.](?!\d)",y['homeTeamBasic']['name'])[0].upper())
                vMix.setValue('battingTeamName', re.split("\s|(?<!\d)[,.](?!\d)",y['awayTeamBasic']['name'])[0].upper())
            if y['inningsIndex'] > 0:
                # have a first Innings score
                vMix.setValue('firstInningsScore',y['inningsScorecards'][0]['stats']['score'])
            else:
                vMix.setValue('firstInningsScore','0')
            vMix.setValue('extraPoints',y['inningsScorecards'][-1]['stats']['extraPoints'])
        elif y.get('methodCaller') == 'getDuckworthLewisStern':
            logger.info(f'CricHQ.Scores1.computegetScorecard : getDuckworthLewisStern : {str(scorecardstr)}')
            vMix.setValue('oversRemaining',int(y['oversRemainingIncludingBreaks']))
            vMix.setValue('dlsParScore',y['parScore'])
        else:
            logger.error(f'methodCaller {y.get("methodCaller")} not defined!')


def cricHQServer():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((socket.gethostname(), 9090))
    #s.bind(('192.168.200.61', 9090))
    s.listen(5)
    while True:
        # now our endpoint knows about the OTHER endpoint.
        logger.info('Waiting %s...' % s)
        clientsocket, address = s.accept()
        print(f"Connection from {address} has been established.")
        with clientsocket:
            #req = createReq('{"method": "getScorecard", "apiVersion": "1.1.2" }')
            
            # req = '{"method": "getScorecard", "apiVersion": "1.1.2" }'
            # send_msg2(clientsocket,req)

            msg = recv_msg2(clientsocket)
            logger.info('Received : %s',msg)
            
            logger.info('Send request getScorecard after inital client connection')
            #clientsocket.sendall(req)
            send_msg2(clientsocket,'{"method": "getScorecard", "apiVersion": "1.1.2" }')
            logger.info('Now what we get back...')
            getScorecard = recv_msg2(clientsocket)
            logger.info('getScorecard : %s',getScorecard)
            computegetScoreCard(getScorecard)

            send_msg2(clientsocket,'{"method": "getDuckworthLewisStern", "apiVersion": "1.1.2" }')
            getDuckworthLewisStern = recv_msg2(clientsocket)
            logger.info('getDuckworthLewisStern : %s',getDuckworthLewisStern)
            computegetScoreCard(getDuckworthLewisStern)

            send_msg2(clientsocket,'{"method": "getMatchScoreView", "apiVersion": "1.1.2" }')
            getMatchScoreView = recv_msg2(clientsocket)
            logger.info('getMatchScoreView : %s',getMatchScoreView)
            send_msg2(clientsocket,'{"method": "getTickerTape", "apiVersion": "1.1.2" }')
            getTickerTape = recv_msg2(clientsocket)
            logger.info('getTickerTape : %s',getTickerTape)
            

        logger.debug('clientsocket closed')    



# MAIN!!!
if __name__ == "__main__":
    # https://stackoverflow.com/questions/38537905/set-logging-levels
    with open('logging.yaml','rt') as f:
            config=yaml.safe_load(f.read())
            f.close()
    logging.config.dictConfig(config)
    logger=logging.getLogger(__name__)
    logger.info("CricHQ interface is starting...")
    HEADERSIZE = 8

    logger.debug('Debug')
    logger.info('Info')

    vMix = VMix()
    cricHQServer()