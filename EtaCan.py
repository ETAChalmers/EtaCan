""" Module containing classes relevant to CAN communication. """
import struct
import datetime
import socket
import threading

class Packet(object):
    """ Class to describe can packets as well as encoding/decoding of can frames. """
    can_frame_format = "=IB3x8s"
    can_frame_size = struct.calcsize(can_frame_format)

    def __init__(self, can_id, data, timestamp=None):
        self.can_id = can_id
        self.dlc = len(data)
        self.data = data.ljust(self.dlc, b'\x00')

        if timestamp:
            self.timestamp = timestamp
        else:
            self.timestamp = datetime.datetime.now().isoformat()

    @classmethod
    def consume(cls, frame, timestamp=None):
        """ Method returning a class containing the decoded packet. """
        can_id, dlc, data = struct.unpack(cls.can_frame_format, frame)
        cls.can_id = can_id
        cls.dlc = dlc
        cls.data = data[:dlc]

        if timestamp:
            cls.timestamp = timestamp
        else:
            cls.timestamp = datetime.datetime.now().isoformat()

        return cls(cls.can_id, cls.data, cls.timestamp)

    def to_frame(self):
        """ Method encoding the can data into a CAN frame, ready to send. """
        return struct.pack(self.can_frame_format, self.can_id, self.dlc, self.data)

    def __str__(self):
        return 'CAN packet: timestamp={0} can_id={1:x}, can_dlc={2:x}, data={3}'.format(
            self.timestamp, self.can_id, self.dlc, ''.join(" {0:02x}".format(x) for x in self.data))

class Socket(object):
    """ Handles general functionality for CAN sockets. """
    def __init__(self, socket_name):
        self.socket_name = socket_name
        self.socket = None

    def open(self):
        """ Opens a CAN socket for reading and writning. """
        if self.socket == None:
            self.socket = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
            self.socket.bind((self.socket_name,))

    def close(self):
        """ Closes the CAN socket and removes the socket object. """
        if self.socket:
            self.socket.close()
            self.socket = None

    def send(self, pkt):
        """ Send CAN packet, should be fed with Packet class packet. """
        if self.socket:
            try:
                self.socket.send(pkt.to_frame())
            except OSError:
                # Failed to send CAN frame.
                pass

    def receive(self):
        """ Receive a CAN packet for further processing. Blocking. """
        if self.socket:
            try:
                can_frame, _ = self.socket.recvfrom(Packet.can_frame_size)
                can_packet = Packet.consume(can_frame)
                return can_packet
            except OSError:
                # Failed to use CAN socket.
                pass

class ThreadedSocket(Socket):
    """ Methods for creating and maintaining a threaded socket server. """
    def __init__(self, interface):
        """ Initialise the super class, Socket. Then the class specific stuff. """
        super().__init__(interface)
        self.callbacks = []
        self.socket_thread = None
        self.shutdown = threading.Event()

    def add_callback(self, function_object):
        """ Add function to be called on received packet.
            The subscriber function must be able to hande Packet class format.
            Note that the callback function must not take too long time to execute.
        """
        self.callbacks.append(function_object)

    def thread_worker(self):
        """ Executes callbacks when given a CAN packet. """
        self.open()

        while(self.shutdown.is_set() == False):
            can_packet = self.receive()

            for subscriber_fcn in self.callbacks:
                subscriber_fcn(can_packet)

        self.close()

    def start_thread(self):
        """ Starts socket thread. """
        self.socket_thread = threading.Thread(target=self.thread_worker)
        self.socket_thread.start()

    def stop_thread(self):
        """ Stop socket thread, hopefully. """
        self.shutdown.set()
        self.socket_thread.join()
        self.socket_thread = None
