# Modified version for Python3.

# scratra ~ 0.3
# greatdane ~ easy python implementation with scratch
# inspired by sinatra(sinatrarb.com) ~ code snippets from scratch.py(bit.ly/scratchpy)
import socket
import re
from errno import *
from array import array
import threading

# Errors from scratch.py
class ScratchConnectionError(Exception):
    pass
class ScratchNotConnected(ScratchConnectionError):
    pass
class ScratchConnectionRefused(ScratchConnectionError):
    pass
class ScratchConnectionEstablished(ScratchConnectionError):
    pass
class ScratchInvalidValue(Exception):
    pass

broadcast_map = []
update_map = []
start_list = []
end_list = []
scratchSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

runtime_quit = 0
scratchInterface = None

# Implementation for Scratch variables
class RemoteSensors:
    sensor_values = {}
    def __setitem__(self, sensor_name, value):
        if isinstance(value, str):
            v = Scratch.toScratchMessage('sensor-update "' + sensor_name +'" "'+value+'"')
            self.sensor_valueues[sensor_name] = value
            scratchSocket.send(v)
        elif isinstance(value, int) or isinstance(value, float):
            v = Scratch.toScratchMessage('sensor-update "' + sensor_name +'" ' + str(value))
            self.sensor_valueues[sensor_name] = value
            scratchSocket.send(v)
        else:
            raise ScratchInvalidValue(sensor_name + ': Incorrect attempted value')
    def __getitem__(self, sensor_name):
        return self.sensor_values[sensor_name]

# For general convenience, scratch interface
class Scratch:

    # Variables interface
    sensor = RemoteSensors()
    var_values = {}

    # Broadcast interface
    def broadcast(self, *broadcasts):
        for broadcast_name in broadcasts:
            scratchSocket.send(self.toScratchMessage('broadcast "' + broadcast_name + '"'))

    # Variable interface
    def var(self, var_name):
        return self.var_values[var_name]

    @staticmethod
    def toScratchMessage(cmd):
        n = len(cmd)
        a = []
        a.append(((n >> 24) & 0xFF))
        a.append(((n >> 16) & 0xFF))
        a.append(((n >> 8) & 0xFF))
        a.append((n & 0xFF))
        b = ''
        for c in a:
            b += chr(c)
        return bytes(b+cmd,'UTF-8')

    @staticmethod
    def atom(msg):
        try:
            return int(msg)
        except:
            try:
                return float(msg)
            except:
                return msg.strip('"')

def run(host='localhost', poll=True,
        msg="Scratra -> Connected\n-> 'stop' to quit",console=True):
    runClass(host, poll, msg, console).start()

# actual threading process
class runClass(threading.Thread):

    def __init__(self, host, poll, msg, console):
        self.host = host
        self.poll = poll
        self.msg = msg
        self.console = console
        threading.Thread.__init__(self)

    def run(self):
        host = self.host
        poll = self.poll
        port = 42001
        console = self.console
        while True:
            try:
                scratchSocket.connect((host, port))
            # Except series from scratch.py
            except socket.error as error:
                (err, msge) = error
                if err == EISCONN:
                    raise ScratchConnectionEstablished('Already connected to Scratch')
                elif poll == True:
                    continue
                elif err == ECONNREFUSED:
                    raise ScratchConnectionRefused('Connection refused, \
                                        try enabling remote sensor connections')
                else:
                    raise ScratchConnectionError(msge)
            scratchInterface = Scratch()
            break

        if console:
            run_console(self.msg).start()
        for func in start_list:
            func(scratchInterface)
        while not runtime_quit:
            try:
                msg = scratchSocket.recv(1024)
            except socket.error as error:
                (errno,message) = error
                raise ScratchConnectionError(errno, message)
            if msg:
                msg = msg.decode("utf-8")
                # If the message is not a sensor-update, but a broadcast
                if msg.find('sensor-update')==-1 and 'broadcast' in msg:
                    msg = msg[15:-1]
                    for (regex,func) in broadcast_map:
                        # check weather whole line is matched.
                        if regex.match(msg) != None and regex.match(msg).end() == len(msg):
                            func(scratchInterface,msg)

                # Otherwise, it must be a sensor-update
                else:
                    msg = msg[4:]
                    if 'sensor-update' in msg:
                        msg = msg.split()[1:]
                        i = 0
                        while i < len(msg)-1:
                            var = scratchInterface.atom(msg[i])
                            val = scratchInterface.atom(msg[i+1])
                            scratchInterface.var_values[var] = val
                            for (regex,func) in update_map:
                                if regex.match(var) != None and regex.match(var).end() == len(var):
                                    func(scratchInterface,var,val)
                            i+=2

class run_console(threading.Thread):
    def __init__(self, msg):
        self.msg = msg
        threading.Thread.__init__(self)

    def run(self):
        global runtime_quit
        print(self.msg)
        while not runtime_quit:
            cmd = input('-> ')
            if cmd == 'stop':
                runtime_quit = 1
                print('-> Quitting')
                for func in end_list:
                    func(scratchInterface)


# For user convenience, decorator methods
# When Scratch broadcasts this...
#  match is re.match.
# @broadcast('scratch_broadcast')
# def func(scratch,msg): ....
class broadcast:
    # broadcast is regular expression string.
    def __init__(self, broadcast):
        self.b = broadcast

    def __call__(self, func):
        broadcast_map.append((re.compile(self.b),func))

# When this variable is updated...
# @update('variable')
# def func(scratch, value): ...
class update:
    def __init__(self, update):
        self.u = update

    def __call__(self, func):
        update_map.append((re.compile(self.u),func))

# When we start listening...
# @start
# def func(scratch): ...
def start(func):
    if func not in start_list:
        start_list.append(func)

# When we stop listening
# @end
# def func(scratch): ...
def end(func):
    if func not in end_list:
        end_list.append(func)
