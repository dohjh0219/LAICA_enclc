#!/usr/bin/env python3
"""
Usage:
    python3 log_to_csv.py
    python3 log_to_csv.py -p /dev/ttyUSB0 -o output.csv
    Ctrl+C to stop
"""

import argparse
import csv
import sys
import time
from datetime import datetime

import serial

HEADER = ('timestamp_s', 'elapsed_s', 'lc_raw', 'lc_mv', 'enc_deg', 'enc_rev', 'enc_rpm')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port',   default='/dev/cu.usbmodem1401')
    parser.add_argument('-b', '--baud',   type=int, default=115200)
    parser.add_argument('-o', '--output', default=None)
    args = parser.parse_args()

    if args.output is None:
        args.output = f"sensors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    try:
        ser = serial.Serial(args.port, args.baud, timeout=2.0)
    except serial.SerialException as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)

    ser.reset_input_buffer()
    t_start = time.time()
    count = 0
    print(f'Logging to {args.output} ... Ctrl+C to stop')

    try:
        with open(args.output, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(HEADER)

            while True:
                line = ser.readline().decode('ascii', errors='ignore').strip()
                if not line.startswith('$SENSORS,'):
                    continue
                parts = line[len('$SENSORS,'):].split(',')
                if len(parts) != 5:
                    continue
                now = time.time()
                writer.writerow([f'{now:.4f}', f'{now - t_start:.4f}'] + parts)
                count += 1

    except KeyboardInterrupt:
        pass
    finally:
        ser.close()

    print(f'Saved {count} rows → {args.output}')


if __name__ == '__main__':
    main()
