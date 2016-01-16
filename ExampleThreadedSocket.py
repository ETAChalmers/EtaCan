import EtaCan
import signal
import sys
import threading

def printpacket(pkg):
    """ Helper function to print CAN packet contents. """
    print(pkg)

shutdown = threading.Event()

def main():
    socket_can = EtaCan.ThreadedSocket('vcan0')
    socket_can.add_callback(printpacket)
    socket_can.start_thread()

    shutdown.wait() # Wait for shutdown signal.

    socket_can.stop_thread() # Stop worker thread, then we wait.

def signal_handler(signal, frame):
    shutdown.set()
    print("Exiting.")

if (__name__ == '__main__'):
    signal.signal(signal.SIGINT, signal_handler)
    main()
    sys.exit(0)
