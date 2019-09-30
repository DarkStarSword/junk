#!/bin/sh

# Reset filesystem permissions in Windows that tend to get randomly messed up
# every now and then for no apparent reason. Using icacls is the most reliable
# method I've found, though in some cases the takeown command may help as well:
# takeown /F file /R

icacls.exe "$@" /T /Q /C /RESET
