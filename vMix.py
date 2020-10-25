'''
This module provides the interface to vMix

'''
import logging, logging.config
import yaml
from lxml import etree
import sys
import datetime, time
import socket

class VMix:
    def __init__(self, ip='127.0.0.1'):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('{} initialized')
        #print('************************')
        
        self.vMixIP = ip
        #self._NameValues = {'TCSld460' : { 'current' : 'BAT NAME 1', 'pending' : 'BAT NAME 1', 'inputs' : ['c3998cb4-afbc-4411-b1b9-c3dc10f02d4d']}}
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.vMixXML = ''
        self.vMixXMLtime = datetime.datetime.now()
        self._desired = {}
        self._actual = {}
        #self._refresh()
    def _connect(self):
        try:
            self.s.connect((self.vMixIP, 8099))
            self.logger.info(f'{self.s.recv(1024)}')
            self._execute('XML\r\n')    # whenever we connect the _execute will then call the xml processor 
        except ConnectionRefusedError as e:
            self.logger.error(f'VMix._connect : Error with _connect : ConnectionRefusedError {e}')
            return False
        except:
            self.logger.error(f'VMix._connect : Error with _connect : {str(sys.exc_info()[0])}')
            raise
        #self.logger.info(f'{self.s.recv(1024)}')
    def _execute(self, command, retry=3):
        if command[:-2] != '\r\n':
            command += '\r\n'
        for i in range(retry):
            if self.__execute(command):
                self.logger.debug(f'_execute retry count {i}')
                break
        
    def __execute(self, command, _errCount=0):
        self.logger.info(f'VMix._execute : command : {command}')
        #self.s.sendall(bytes(command,"utf-8"))
        try:
            self.s.sendall(bytes(command,"utf-8"))
        except OSError as e:
            self.logger.debug(f'VMix._execute : Socket not open so reconnect... {e}')
            self._connect()
            #self._execute(command)
            return False
        if command.startswith('FUNCTION'):
            self.s.setblocking(0)
            self.s.settimeout(0.5)
            try:
                response = self.s.recv(25)
                response = response.decode('utf-8')
            except TimeoutError:
                response = ''
                self.logging.error(f'Timed out waiting for a response from the vMix socket')
            self.logger.debug(f'VMix._execute : response from {command[:-2]} : {response}')
            if 'FUNCTION OK Completed' in response:
                self.logger.info(f'VMix._execute : command : {command[:-2]} : OK')
                return True
            else:
                self.logger.error(f'VMix._execute : command : {command[:-2]} : {response}')
                return response
        elif command.startswith('XML'):
            done = False
            new_msg = True
            full_xml = ''
            while not done:
                try:
                    data = self.s.recv(1024)
                except ConnectionAbortedError:
                    self.logger.error(f'vMixXML : Connection Aborted')
                    xml = None
                    break
                xml = data.decode('utf-8')
                if new_msg:
                    # What is our length then?
                    msglen = int(xml[xml.find('XML ') + 4 : xml.rfind('\r\n')])  # 4 is length of 'XML '
                    new_msg = False
                    self.logger.debug(f'vMixXML : msglen is {msglen}')
                else:
                    full_xml += xml
                if len(full_xml) >= msglen:
                    done = True
                    self.logger.debug(f'VMix.__execute : length full_xml {len(full_xml)} and msglen {msglen}')
                    break
                self.logger.debug(f'vMixXML : length {len(full_xml)}')
            self.logger.info(f'vMixXML : returning {full_xml}')
            self._processXML(full_xml)
            return full_xml
        else:
            response = self.s.recv(50)
            response = response.decode('utf-8')
            self.logger.error(f'VMix._execute : NOT SURE HOW TO HANDEL THIS COMMAND : {command[:-2]} : Response : {response}')
        return

    def _processXML(self, xml):
        # *** now lets build our mega dict!
        starttime = datetime.datetime.now()
        self.logger.info(f'VMix._processXML start time : {starttime}')
        self.vMixXML = xml
        # Just going to build _disired and _actual on the fly by request instead
        self.logger.info(f'VMix._processXML done in : {datetime.datetime.now() - starttime}')
        pass
    def setValue(self, name, value):
        self._desired[name] = value
        self.logger.info(f'VMix.setValue : _desired = {self._desired}')
        try:
            if self._actual[name] is not self._desired[name]:
                self.logger.info(f'VMix.setValue need to update {name} from {self._actual[name]} to {self._desired[name]}')
        except KeyError as error:
            self._actual[name] = ''
            self.logger.info(f'VMix.setValue need to update {name} from UNKOWN to {self._desired[name]}')
        
        #* Put this bit in its own thread to allow high speed data like timing to be push at vMix faster than it can be updated
        if (datetime.datetime.now() - self.vMixXMLtime) >  datetime.timedelta(minutes = 1):
            self.logger.info(f'VMix._processValues Refresh vMIX XML as it is stale {str((datetime.datetime.now() - self.vMixXMLtime))}')
            self._execute('XML')
        starttime = datetime.datetime.now()
        self.logger.info(f'VMix._processValues start time : {starttime}, {str(self._desired)} {self.vMixXML}')
        for k, v in self._desired.items():
            if self._desired[k] is not self._actual[k]:
                # Do find and update
                if self.vMixXML == '':# or 
                    #* Improve to update old XML
                    self.logger.info(f'VMIX.Update : no XML')
                    self._execute('XML')
                else:
                    root = etree.fromstring(self.vMixXML)
                    for element in root.xpath(f"//text[@name='{k}']"):
                        self._execute(f'FUNCTION SetText Input={element.getparent().get("key")}&SelectedName={k}&Value={v}')
        self.logger.info(f'VMix._processValues done in : {datetime.datetime.now() - starttime}')

    def _command(self, command):
        response = ''
        return response

# MAIN!!!
if __name__ == "__main__":
    # https://stackoverflow.com/questions/38537905/set-logging-levels
    with open('logging.yaml','rt') as f:
            config=yaml.safe_load(f.read())
            f.close()
    logging.config.dictConfig(config)
    logger=logging.getLogger(__name__)
    logger.info("vMix interface is starting...")

    vMix = VMix()
    vMix.setValue('TCSld460','bob')
    vMix.setValue('TCSld490','fred')
    vMix.setValue('TCSld460','tim')
    vMix.setValue('NoThere','another')
    vMix.setValue('BAT1','another')
    
    
    