#!/usr/bin/env python3

import signal
import time

running = True

def stop_service(signum, frame):
    global running
    running = False

signal.signal(signal.SIGTERM, stop_service)
signal.signal(signal.SIGINT, stop_service)

print("Webbie resident service online.", flush=True)

while running:
    time.sleep(30)

print("Webbie resident service shutting down.", flush=True)
