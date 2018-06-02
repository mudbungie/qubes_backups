### This is a one-liner, to be run manually from dom0 to deploy this script. 
# vm name for the backup domain implied here to be backups. Change as needed.
qvm-run -a -p backups 'git clone https://github.com/mudbungie/qubes_backups ; tar -cz qubes_backups | cat' > f.tar.gz && tar xzf f.tar.gz && rm f.tar.gz
