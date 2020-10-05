'''
This module provides the interface to vMix

'''
import logging, logging.config
import yaml
import xml
import sys
import datetime, time
import socket

class VMix:
    def __init__(self, ip='127.0.0.1'):
        self.vMixIP = ip
        self._NameValues = {'TCSld460' : { 'current' : 'BAT NAME 1', 'pending' : 'BAT NAME 1', 'inputs' : ['c3998cb4-afbc-4411-b1b9-c3dc10f02d4d']}}
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self._refresh()
    def _connect(self):
        try:
            self.s.connect((self.vMixIP, 8099))
            logger.info(f'{self.s.recv(1024)}')
            self._execute('XML\r\n')    # whenever we connect the _execute will then call the xml processor 
        except ConnectionRefusedError as e:
            logger.error(f'VMix._connect : Error with _connect : ConnectionRefusedError {e}')
            return False
        except:
            logger.error(f'VMix._connect : Error with _connect : {str(sys.exc_info()[0])}')
            raise
        #logger.info(f'{self.s.recv(1024)}')
    def _execute(self, command, retry=3):
        for i in range(retry):
            if self.__execute(command):
                logger.debug(f'_execute retry count {i}')
                break
        
    def __execute(self, command, _errCount=0):
        logger.info(f'VMix._execute : command : {command}')
        #self.s.sendall(bytes(command,"utf-8"))
        try:
            self.s.sendall(bytes(command,"utf-8"))
        except OSError as e:
            logger.debug(f'VMix._execute : Socket not open so reconnect... {e}')
            self._connect()
            #self._execute(command)
            return False
        if command.startswith('FUNCTION'):
            response = self.s.recv(25)
            response = response.decode('utf-8')
            logger.debug(f'VMix._execute : response from {command[:-2]} : {response}')
            if 'FUNCTION OK Completed' in response:
                logger.info(f'VMix._execute : command : {command[:-2]} : OK')
                return True
            else:
                logger.error(f'VMix._execute : command : {command[:-2]} : {response}')
                return response
        elif command.startswith('XML'):
            done = False
            new_msg = True
            full_xml = ''
            while not done:
                try:
                    data = self.s.recv(1024)
                except ConnectionAbortedError:
                    logger.error(f'vMixXML : Connection Aborted')
                    xml = None
                    break
                xml = data.decode('utf-8')
                if new_msg:
                    # What is our length then?
                    msglen = int(xml[xml.find('XML ') + 4 : xml.rfind('\r\n')])  # 4 is length of 'XML '
                    new_msg = False
                    logger.debug(f'vMixXML : msglen is {msglen}')
                else:
                    full_xml += xml
                if len(full_xml) >= msglen:
                    done = True
                    logger.debug(f'VMix.__execute : length full_xml {len(full_xml)} and msglen {msglen}')
                    break
                logger.debug(f'vMixXML : length {len(full_xml)}')
            logger.info(f'vMixXML : returning {full_xml}')
            self._processXML(full_xml)
            return full_xml
        else:
            response = self.s.recv(50)
            response = response.decode('utf-8')
            logger.error(f'VMix._execute : NOT SURE HOW TO HANDEL THIS COMMAND : {command[:-2]} : {response}')
        return

    def _processXML(self, xml):
        # *** now lets build our mega dict!
        starttime = datetime.datetime.now()
        logger.info(f'VMix._processXML start time : {starttime}')

        logger.info(f'VMix._processXML done in : {datetime.datetime.now() - starttime} : result is : {self._NameValues}')
        pass
    def setValue(self, name, value):
        try:
            self._NameValues[name]['pending'] = value
            logger.debug(f'VMix.setValue : self._NameValues[name] {self._NameValues[name]}')
        except KeyError:
            logger.error(f'VMix.setValue : KeyError bad name passed : {name}')
            return False
        self._execute('FUNCTION SetText Input=1&SelectedName=SCORETOTAL&Value=cc\r\n')
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
    print(vMix._NameValues)
    