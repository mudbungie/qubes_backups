#!/usr/bin/env python3

# This software is licensed under the GPLv3. You should have recieved a copy
# of the GPLv3 along with the software. The GPLv3 is also available at
# https://www.gnu.org/licenses/gpl-3.0.txt
# Copyright 2017 Mudbungie 
# Please contact the author mudbungie@mudbungie.net

# This is a backup script for files in Qubes images. Requires either execution 
# in dom0 or valid qubes-rpc policies (untested). 
# It reads a JSON config file, specified by the first argument. The config will
# specify files inside of VMs that will be added to the backup, as well as a 
# backup destination VM, to which the files will be copied. It will optionally
# include a command to execute once backup is complete, as well as optionally
# specify a password, to encrypt the backup. If a password is not specified, 
# it will be prompted for. If the post backup command includes the string {!},
# that will be replaced with the name of the backup directory.
# WARNING: This whole files in RAM, which can be problematic for large files.

from sys import argv, exit
from subprocess import run, PIPE
from datetime import datetime
import re
import logging
import json

# Get basic configuration stuff
def get_config():
	try:
		with open(argv[1]) as f:
			config = json.load(f)
	except IndexError:
		exit('No configuration file specified.')
	except FileNotFoundError:
		exit('No configuration file at specified path.')
	except json.decoder.JSONDecodeError:
		exit('Invalid JSON as specified path.')
	
	# Check for the mandatory config components.
	if not 'paths' in config:
		exit('Mandatory configuration option missing: "paths".')
	elif not 'backup_vm' in config:
		exit('Mandatory configuration option missing: "backup_vm".')
	
	# Handle optional config components.
	if not 'post_backup_command' in config:
		config['post_backup_command'] = False
	if 'password' in config:
		config['password'] = json.dumps(config['password'])
	else:
		from getpass import getpass
		config['password'] = getpass('Enter password: ')
	return config

# Subprocess wrapper for qvm-run, passing input back and forth.
def vm_run(vm_name, command, stdin=None):
	if stdin:
		stdin = stdin.encode()
	# -a turns on the VM, if it's off; -p passes pipes back and forth. 
	args = ['qvm-run', '-a', '-p', '{}'.format(vm_name), "{}".format(command)]
	command = run(args,	input=stdin, stdout=PIPE)
	if command.returncode == 0:
		return command.stdout.decode()
	else:
		logging.warn('Command returned non-zero status code: {}'.format(command))

# Takes a path (vm_name:/path/to/file/or/dir), tars, encrypts, returns as string
def encrypt_path(path, password):
	vm_name = path.split(':')[0]
	vm_path = re.sub('^[\w_-]+:', '', path)
	print(vm_path)
	# 
	command = 'tar cfz - {} | gpg --cipher-algo AES256 -acqo - --passphrase {} --batch'.\
		format(vm_path, password)
	tarball = vm_run(vm_name, command)
	return tarball

# Takes a path and the password, returns dict of paths:encrypted tarballs.
def encrypt_all(paths, password):
	# The path will be in format 'vm_name:/path/to/file'
	enc_files = {}
	for path in paths:
		tarball = encrypt_path(path, password)
		if tarball:
			enc_files[path + '.tar.gz.gpg'] = tarball
		else:
			logging.error('Failed to create backup for path {}'.format(path))
	return enc_files

# Returns nothing. Sends files to backup vm.
def send_to_backup_vm(vm_name, enc_files, post=None):
	# So that I don't have to keep passing the backup name.
	def bvm_run(*args, **kwargs):
		vm_run(vm_name, *args, **kwargs)

	# Colons are scrubbed in this section exclusively for ease of tar.
	# [singing] excessive string manipulation [/singing]
	now = ''.join(datetime.now().isoformat().split('.')[:-1]).replace(':', '_')
	backup_dir = 'backup_{}'.format(now)
	bvm_run('mkdir {}'.format(backup_dir))
	for name, enc_f in enc_files.items():
		# Gotta scrub illegal pathnames.
		name = name.replace(':', '-').replace('/', '_') 
		bvm_run('cat > {}/{}'.format(backup_dir, name), stdin=enc_f)
	if post:
		post = post.replace('{!}', backup_dir)
		print('Executing post-backup command: {}'.format(post))
		bvm_run(post)

if __name__ == '__main__':
	logging.basicConfig(format='%(levelname)s:%(message)s',level=logging.DEBUG) 
	config = get_config()
	enc_files = encrypt_all(config['paths'], config['password'])
	send_to_backup_vm(config['backup_vm'], enc_files, 
		post=config['post_backup_command'])
