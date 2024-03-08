#!/usr/bin/env python3

import sys
from time import sleep

print('Called management.py')

try:
    if sys.argv[1] == 'runserver':
        print('Running fake server')
        while True:
            sleep(60) 
except:
    pass