#! /usr/bin/env python3

from zeroconf import ServiceInfo, Zeroconf, socket
import logging
#import server.py


def start():
	global localHTTP, zeroconf, info, httpthread
	ip = '192.168.0.81'
	logging.info("Local IP is " + ip)

	desc = {'version': '0.1'}
	info = ServiceInfo("_http._tcp.local.",
			"Alexa Device._http._tcp.local.",
			socket.inet_aton(ip), 0, 0, 0,
			'desc', "me.LOCAL_HOST.")
	zeroconf = Zeroconf()
	zeroconf.register_service(info)
	logging.info("Local mDNS is started, domain is " + alexa_params.LOCAL_HOST)
	localHTTP = HTTPServer(("", alexa_params.LOCAL_PORT), alexa_http_config.AlexaConfig)
	httpthread = threading.Thread(target=localHTTP.serve_forever)
	httpthread.start()
	logging.info("Local HTTP is " + alexa_params.BASE_URL)
	alexa_control.start()


def announce_zeroconf(self):
        desc = {'name': 'SigmaTCP',
                'vendor': 'HiFiBerry',
                'version': hifiberrydsp.__version__}
        hostname = socket.gethostname()
        try:
            ip = socket.gethostbyname(hostname)
        except Exception:
            logging.error("can't get IP for hostname %s, "
                          "not initialising Zeroconf",
                          hostname)
            return

        self.zeroconf_info = ServiceInfo(ZEROCONF_TYPE,
                                         "{}.{}".format(
                                             hostname, ZEROCONF_TYPE),
                                         socket.inet_aton(ip),
                                         DEFAULT_PORT, 0, 0, desc)
        self.zeroconf = Zeroconf()
        self.zeroconf.register_service(self.zeroconf_info)

#announce_zeroconf()

#me = SigmaTCPServerMain()


#from six.moves import input
from zeroconf import ServiceBrowser, Zeroconf


class MyListener(object):

    def remove_service(self, zeroconf, type, name):
        print("Service %s removed" % (name,))

    def add_service(self, zeroconf, type, name):
        #info = zeroconf.get_service_info(type, name)
        info = ServiceInfo(
            '_cricviewing._tcp.local.','_myboard._cricviewing._tcp.local.',
            socket.inet_aton('192.168.0.81'), 1234, 0, 0, '_myboard._cricviewing._tcp.local.'
        )
        print("Service %s added, service info: %s" % (name, info))


zeroconf = Zeroconf()
listener = MyListener()
browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)
listener.add_service(zeroconf,'_cricviewing._tcp.local.','_device._cricviewing._tcp.local.')
try:
    input("Press enter to exit...\n\n")
finally:
    zeroconf.close()

