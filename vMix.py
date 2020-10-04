'''
This module provides the interface to vMix

'''
import logging, logging.config
import yaml
import xml
import sys
import socket

class VMix:
    def __init__(self, ip='127.0.0.1'):
        self.vMixIP = ip
        self._NameValues = {'TCSld460' : { 'current' : 'BAT NAME 1', 'pending' : 'BAT NAME 1', 'inputs' : ['c3998cb4-afbc-4411-b1b9-c3dc10f02d4d']}}
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._refresh()
    def _connect(self):
        try:
            self.s.connect((self.vMixIP, 8099))
        except ConnectionRefusedError:
            print(sys.exc_info()[0])
            logger.error(f'VMix._connect : Error with _connect : ConnectionRefusedError {sys.exc_info()[0]}')
        logger.info(f'{self.s.recv(1024)}')
    '''
    except OSError as err:
        print("OS error: {0}".format(err))
    except ValueError:
        print("Could not convert data to an integer.")
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise
    '''


    def _refresh(self):
        self._connect()
        pass
    def setValue(self, name, value):
        try:
            self._NameValues[name]['pending'] = value
            logger.debug(f'VMix.setValue : self._NameValues[name] {self._NameValues[name]}')
        except KeyError:
            logger.error(f'VMix.setValue : KeyError bad name passed : {name}')
            return False
        
        
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
    