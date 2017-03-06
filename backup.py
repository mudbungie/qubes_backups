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
from subprocess import run, PIPE
from datetime import datetime
import re
import logging

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

# Subprocess wrapper for qvm-run, passing input back and forth.
def vm_run(vm_name, command, stdin=None):
	if stdin:
		stdin = stdin.encode()
	# -a turns on the VM, if it's off; -p passes pipes back and forth. 
	args = ['qvm-run', '-a', '-p', '{}'.format(vm_name), "'{}'".format(command)]
	command = run(args,	stdin=stdin, stdout=PIPE)
	if a.returncode == 0:
		return command.stdout.decode()
	else:
		logging.warn('Command returned non-zero status code: {}'.format(command))

# Takes a path (vm_name:/path/to/file/or/dir), tars, encrypts, returns as string
def encrypt_path(path, password):
	vm_name = path.split(':')[0]
	vm_path = re.sub('^\w+:', '', path)
	# 
	command = 'tar cfz - {} | gpg --cipher-algo AES256 -acqo --passphrase {}'.\
		format(vm_path, password)
	tarball = vm_run(command)
	return tarball

# Takes a path and the password, returns dict of paths:encrypted tarballs.
def encrypt_all(paths, password):
	# The path will be in format 'vm_name:/path/to/file'
	enc_files = {}
	for path in paths:
		tarball = encrypt_path(path, password)
		if tarball:
			enc_files[path] = tarball
		else:
			logging.error('Failed to create backup for path {}'.format(path))
	return enc_files

def send_to_backup_vm(vm_name, enc_files):
	# So that I don't have to keep passing the backup name.
	def bvm_run(command):
		vm_run(vm_name, command)

	now = datetime.now().isoformat()
	bvm_run('mkdir backup_{}'.format(now))
	for name, enc_f in enc_files.items():
		# Gotta scrub illegal pathnames.
		name = name.replace('/', '-')
		bvm_run('cat > {}/{}'.format(now, name), stdin=enc_f)

if __name__ == '__main__':
	logging.basicConfig(format='%(levelname)s:%(message)s',level=logging.DEBUG) 
	config, password = get_config()
	enc = encrypt_all(config['paths'], password)
		
	# Before executing anything, get a password, if necessary.
	
