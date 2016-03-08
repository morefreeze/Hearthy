from hearthy import exceptions
from hearthy.tracker import processor
from hearthy.protocol.decoder import decode_packet
from hearthy.protocol.utils import Splitter
import threading
import socketserver, socket
import http.server
import urllib.parse

class HeathyServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    d = {}
    server = {}

    @staticmethod
    def start(ip, port, file_name):
        """start server

        :ip: ip
        :port: port
        :file_name: pcapng file

        """
        start_func = None
        if ip != '' and port > 0:
            server = socketserver.ThreadingTCPServer((ip, port), HeathyServer.HearthyHandler)
            start_func = server.serve_forever
        server_thread = threading.Thread(target=start_func)
        server_thread.daemon = True
        server_thread.start()

        d = HeathyServer.d
        with open(file_name, 'rb') as f:
            parser = hcapng.parse(f)
            begin = next(parser)
            for ts, event in parser:
                if isinstance(event, hcapng.EvClose):
                    if event.stream_id in d:
                        pass
                        # del d[event.stream_id]
                elif isinstance(event, hcapng.EvData):
                    if event.stream_id in d:
                        try:
                            d[event.stream_id].feed(event.who, event.data)
                        except exceptions.BufferFullException:
                            del d[event.stream_id]
                elif isinstance(event, hcapng.EvNewConnection):
                    d[event.stream_id] = HeathyServer.Connection(event.source, event.dest)
        # import pdb; pdb.set_trace()

        server_thread.join()

    class Connection:
        def __init__(self, source, dest):
            self.p = [source, dest]
            self._s = [Splitter(), Splitter()]
            self._t = processor.Processor()

        def feed(self, who, buf):
            for atype, abuf in self._s[who].feed(buf):
                decoded = decode_packet(atype, abuf)
                self._t.process(who, decoded)

        def __repr__(self):
            print('<Connection source={0!r} dest={1!r}'.format(
                self.p[0], self.p[1]))

    class HearthyHandler(http.server.BaseHTTPRequestHandler):
        """Docstring for HearthyHandler. """
        def do_GET(s):
            s.send_response(200)
            # Handler more format, like json.
            s.send_header("Content-type", "text/html")
            s.end_headers()

            server_dict = HeathyServer.d
            wd = {}
            # get the last valid world
            for k in server_dict:
                tmp_wd = server_dict[k]._t._world.transaction()
                # normal world at least 67 items
                if 67 in tmp_wd:
                    wd = tmp_wd

            # sb is string builder for response data.
            sb = ''
            o = urllib.parse.urlparse(s.path)
            d = urllib.parse.parse_qs(o.query)
            func_map = HeathyServer.HearthyHandler.func_map
            if o.path in func_map:
                func = getattr(HeathyServer.HearthyHandler, func_map[o.path])
                sb += '<pre>'
                sb += func(wd, d)
                sb += '</pre>'
            else:
                sb += 'Supported operation are : [' + ','.join(s.func_map.keys()) + "]\n"
                sb += "Your path is: %s" %(o.path)
            s.wfile.write(sb.encode())

        @staticmethod
        def parse_entity(wd, params):
            """return entity detail

            :wd: world
            :params: {id: ['1',]}
            :returns: entity string

            """
            from hearthy.protocol.utils import format_tag_name
            from hearthstone.enums import GameTag
            ret = ''
            ids = params.get('id', [])
            for id in ids:
                id = int(id)
                if id not in wd:
                    ret += "No such id %s" %(id)
                else:
                    for tag, v in wd[id]._tags.items():
                        ret += "{0}: {1}\n".format(format_tag_name(tag), v)
                ret += "\n"
            if len(ids) == 0:
                return 'No such ids %s' %(params.get('id', []))
            # print(ret)
            return ret

        func_map = {
            '/entity': 'parse_entity',
        }

if __name__ == '__main__':
    import sys
    from hearthy.datasource import hcapng

    if len(sys.argv) < 2:
        print('Usage: {0} <hcapng file>'.format(sys.argv[0]))
        sys.exit(1)

    import logging
    logging.getLogger().setLevel(logging.DEBUG)

    ip = ''
    port = 0
    if len(sys.argv) >= 4:
        ip = sys.argv[2]
        port = int(sys.argv[3])
    HeathyServer.start(ip, port, sys.argv[1])

