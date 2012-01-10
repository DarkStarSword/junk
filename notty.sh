#!/bin/sh

export LD_PRELOAD=$PWD/libnotty.so

exec "$@"
