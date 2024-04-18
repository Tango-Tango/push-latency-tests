import argparse
import logging
import signal
import socket
import ssl
import struct
import threading
import time
from dataclasses import dataclass
from typing import TextIO

import certifi
import h2.connection
import h2.events

from .console import console, error_console


def print(*args, **kwargs):
    console.print(*args, **kwargs)


def now():
    return asyncio.get_event_loop().time()


logger = logging.getLogger()
terminate = False
PING_INTERVAL = 2


def signal_handler(sig, frame):
    logger.info("Got SIGINT. Terminating.")
    global terminate
    terminate = True


signal.signal(signal.SIGINT, signal_handler)


def run_test(host: str, port: int, outfile: TextIO):
    ctx = ssl.create_default_context(cafile=certifi.where())
    ctx.set_alpn_protocols(["h2"])
    # Allows you to use an IP address for the hostname
    ctx.check_hostname = False

    sock = socket.create_connection((host, port))
    sock.settimeout(1)
    sock = ctx.wrap_socket(sock, server_hostname=host)

    conn = h2.connection.H2Connection()
    conn.initiate_connection()
    sock.sendall(conn.data_to_send())

    logger.info("Starting threads")
    receiveThread = threading.Thread(target=receive, args=(sock, conn, outfile))
    sendThread = threading.Thread(target=ping, args=(sock, conn))

    receiveThread.start()
    sendThread.start()

    receiveThread.join()
    global terminate
    terminate = True
    sendThread.join()

    logger.info("")

    # cleanup and close the connection
    conn.close_connection()
    sock.sendall(conn.data_to_send())
    sock.close()


def ping(socket, conn):
    logger.info(f"Starting send thread")
    global terminate
    while not terminate:
        payload = struct.pack("Q", time.monotonic_ns())
        conn.ping(payload)
        socket.sendall(conn.data_to_send())
        time.sleep(PING_INTERVAL)


def receive(socket, conn, outfile):
    logger.info("Starting receive thread")
    global terminate
    while not terminate:
        # read raw data from the socket
        try:
            data = socket.recv(65536 * 1024)
        except TimeoutError:
            continue

        if not data:
            break

        # feed raw data into h2, and process resulting events
        events = conn.receive_data(data)
        for event in events:
            if isinstance(event, h2.events.PingAckReceived):
                sent_time_ns = struct.unpack("Q", event.ping_data)[0]
                elapsed_time_ms = (time.monotonic_ns() - sent_time_ns) / 1_000_000
                logger.info("Ping ACK received. latency: %.3f ms", elapsed_time_ms)
                outfile.write(f"{elapsed_time_ms}\n")
                outfile.flush()
            elif isinstance(event, h2.events.ConnectionTerminated):
                logger.info("Connection terminated (GOAWAY)")
                terminate = True
                break
            elif isinstance(event, h2.events.PingReceived):
                logger.info("Incoming ping received")
                socket.sendall(conn.data_to_send())
            else:
                logger.warning(f"Unhandled event: {event}")

        # send any pending data to the server
        socket.sendall(conn.data_to_send())


def main():
    parser = argparse.ArgumentParser(description="Test HTTP latency")
    parser.add_argument(
        dest="host",
        type=str,
        help="The hostname or IP (preferably) of the server",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=443,
        help="The port number to connect to (default: 443)",
    )
    parser.add_argument(
        "-o",
        "--outfile",
        type=argparse.FileType("w"),
        default="-",
        help="Output file (default: stdout)",
    )
    args = parser.parse_args()
    run_test(args.host, args.port, args.outfile)


if __name__ == "__main__":
    main()
