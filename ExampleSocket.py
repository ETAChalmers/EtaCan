import EtaCan
import signal
import sys
import threading

shutdown = threading.Event()
def main():
    s = EtaCan.Socket('vcan0')
    s.open()

    while(shutdown.is_set() == False):
        packet = s.receive()
        print(packet)

    s.close()

def signal_handler(signal, frame):
    shutdown.set()
    print("Exiting.")

if (__name__ == '__main__'):
    signal.signal(signal.SIGINT, signal_handler)
    main()
    sys.exit(0)
