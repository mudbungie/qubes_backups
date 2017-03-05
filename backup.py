#!/usr/bin/env python3

# This software is licensed under the GPLv3. You should have recieved a copy
# of the GPLv3 along with the software. The GPLv3 is also available at
# https://www.gnu.org/licenses/gpl-3.0.txt
# Copyright 2017 Mudbungie 
# Please contact me at mudbungie@mudbungie.net

# This is a backup script for files in Qubes images. Must be executed in dom0,
# because it executes in multiple domains.
# It reads a config file, specified by the first argument. The config will 
# specify files inside of VMs that will be added to the backup. It will 
# optionally also specify a password, to encrypt the backup. If a password is
# not specified, it will be prompted for. 
# WARNING: This whole files in RAM, which can be problematic for large files.

from configobj import ConfigObj
from sys import argv, exit
from os import subprocess
import re

# Get basic configuration stuff
def get_config():
	try:
		config = ConfigObj(argv[1])
	except IndexError:
		exit('No configuration file specified.')
	if not config:
		exit('No configuration file at specified path.')
	# Check for the mandatory config components.
	if not config.kets() & {'backup_vm', 'files'}:
		exit('Invalid configuration file.')
	try:
		password = config['password']
	except KeyError:
		from getpass import getpass
		password = getpass('Enter password: ')
	return config, password

# Wrapper for qvm-run, passing input back and forth.
def vm_run(vm_name, command, pipe_in=None):
	
	

# Takes a path and the password, returns list of encrypted strings. 
def encrypt_all(paths, password):
	# The path will be in format 'vm_name:/path/to/file'
	enc_files = []
	for path in paths:
		vm_name = path.split(':')[0]
		path = re.sub('^\w+:', '', path)
		# If it's a directory, recurse through the files.
		if path.endswith('/'):
			enc_files.extend(encrypt_dir(vm_name, path))
		else:
			enc_files.append(encrypt_file(vm_name, path))
	return enc_files

def encrypt_file(vm_name, path):
	subprocess.run('qvm-run ')
def encrypt_dir():


if __name__ == '__main__':
	config, password = get_config()
	for f in config['files']:
		if 
	
	# Before executing anything, get a password, if necessary.
	
