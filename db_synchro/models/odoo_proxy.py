# See LICENSE file for full copyright and licensing details.

from xmlrpc.client import ServerProxy
import ssl

import logging
_logger = logging.getLogger(__name__)


class RPCProxyOne(object):
    def __init__(self, server, ressource):
        """Class to store one RPC proxy server."""
        self.server = server

        if server.server_protocol == 'http':
            http = 'http://'
            context = None
        elif server.server_protocol == 'https':
            http = 'https://'
            context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS)
        elif server.server_protocol == 'https_1':
            http = 'https://'
            context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLSv1)
        elif server.server_protocol == 'https_1_1':
            http = 'https://'
            context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLSv1_1)
        elif server.server_protocol == 'https_1_2':
            http = 'https://'
            context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLSv1_2)

        local_url = '%s%s:%d/xmlrpc/common' % (http, server.server_url, server.server_port)
        rpc = ServerProxy(local_url, context=context)
        self.uid = rpc.login(server.server_db, server.login, server.password)
        local_url = '%s%s:%d/xmlrpc/object' % (http, server.server_url, server.server_port)
        self.rpc = ServerProxy(local_url, context=context)
        self.ressource = ressource

    def __getattr__(self, name):
        return lambda *args, **kwargs: self.rpc.execute(self.server.server_db,
                                                        self.uid,
                                                        self.server.password,
                                                        self.ressource, name,
                                                        *args)


class RPCProxy(object):
    """Class to store RPC proxy server."""

    def __init__(self, server):
        self.server = server

    def get(self, ressource):
        return RPCProxyOne(self.server, ressource)
