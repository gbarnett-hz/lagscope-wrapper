#!/usr/bin/env bash

# default port is 6001
lagscope/build/lagscope -r &
fastapi run main.py --port 4000
