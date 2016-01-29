import sys
import socket
import select
import random
from itertools import cycle


SERVER_POOL = [('localhost', 8888), ('localhost', 9999)]

ITER = cycle(SERVER_POOL)


def round_robin(iterator):
    return next(iterator)


class LoadBalancer:

    sockets_mapping = {}
    sockets_list = []

    def __init__(self, ip, port, algorithm='random'):
        self.ip = ip
        self.port = port
        self.algorithm = algorithm

        # init client socket
        self.client = socket.socket()
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.client.bind((self.ip, self.port))
        print 'init socket: %s' % str(self.client.getsockname())
        self.client.listen(10)
        self.sockets_list.append(self.client)

    def start(self):
        while True:
            read_list, write_list, exception_list = select.select(self.sockets_list, [], [])
            for s in read_list:
                print 'hello: %s' % str(s.getsockname())
                if s is self.client:
                    print '='*40 + 'flow start' + '='*40
                    self.on_accept()
                else:
                    try:
                        data = s.recv(4096)
                        print data
                        if data:
                            self.on_recv(s, data)
                        else:
                            self.on_close(s)
                            break
                    except:
                        self.on_close(s)
                        break

    def on_accept(self):
        client_socket, client_addr = self.client.accept()
        print 'client connected: %s <===> %s' % (client_addr, str(self.client.getsockname()))

        # select server
        server_ip, server_port = self.select_server(SERVER_POOL, self.algorithm)
        # create server socket
        server_socket = socket.socket()
        try:
            server_socket.connect((server_ip, server_port))
            print 'init server socket: %s' % str(server_socket.getsockname())
            print 'server connected: %s <===> %s' % (str(server_socket.getsockname()), str(client_socket.getsockname()))
        except:
            print 'cannot establish connection %s <===> %s' % (str(server_socket.getsockname()), str(client_socket.getsockname()))
            client_socket.close()
            return

        self.sockets_list.append(server_socket)
        self.sockets_list.append(client_socket)

        self.sockets_mapping[server_socket] = client_socket
        self.sockets_mapping[client_socket] = server_socket

    def on_close(self, s):
        remote_socket = self.sockets_mapping[s]
        self.sockets_list.remove(s)
        self.sockets_list.remove(remote_socket)
        remote_socket.close()
        s.close()
        del self.sockets_mapping[s]
        del self.sockets_mapping[remote_socket]

    def on_recv(self, s, data):
        print 'receiving packet: %s data= %s' % (s.getsockname(), data)
        remote_socket = self.sockets_mapping[s]
        remote_socket.send(data)
        print 'sending packet: %s data= %s' % (remote_socket.getsockname(), data)

    def select_server(self, server_pool, algorithm='random'):
        print 'selecting'
        if algorithm == 'random':
            return random.choice(server_pool)
        elif algorithm == 'round robin':
            return round_robin(ITER)
        else:
            raise Exception('unknown algorithm')

if __name__ == '__main__':
    try:
        LoadBalancer('localhost', 5555, 'round robin').start()
    except KeyboardInterrupt:
        print "Ctrl-C stop load balancer"
        sys.exit(1)
