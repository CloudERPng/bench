import click

import os, shutil, tempfile
import os.path as osp
import contextlib
import logging

from datetime import datetime

from bench.utils import which, exec_cmd

log = logging.getLogger(__name__)
log.setLevel(logging.ERROR)

def print_bench_version(ctx, param, value):
	"""Prints current bench version"""
	if not value or ctx.resilient_parsing:
		return

	import bench
	click.echo(bench.__version__)
	ctx.exit()

@click.group()
@click.option('--version', is_flag=True, is_eager=True, callback=print_bench_version, expose_value=False)
def bench_command(bench_path='.'):
	"""Bench manager for Frappe"""
	import bench
	from bench.app import get_current_frappe_version
	from bench.utils import setup_logging

	bench.set_frappe_version(bench_path=bench_path)
	setup_logging(bench_path=bench_path)


from bench.commands.make import init, get_app, new_app, remove_app, new_site
bench_command.add_command(init)
bench_command.add_command(get_app)
bench_command.add_command(new_app)
bench_command.add_command(remove_app)
bench_command.add_command(new_site)


from bench.commands.update import update, retry_upgrade, switch_to_branch, switch_to_master, switch_to_develop
bench_command.add_command(update)
bench_command.add_command(retry_upgrade)
bench_command.add_command(switch_to_branch)
bench_command.add_command(switch_to_master)
bench_command.add_command(switch_to_develop)

from bench.commands.utils import (start, restart, set_nginx_port, set_ssl_certificate, set_ssl_certificate_key, set_url_root,
	set_mariadb_host, set_default_site, download_translations, shell, backup_site, backup_all_sites, release, renew_lets_encrypt,
	disable_production, bench_src, prepare_staging)
bench_command.add_command(start)
bench_command.add_command(restart)
bench_command.add_command(set_nginx_port)
bench_command.add_command(set_ssl_certificate)
bench_command.add_command(set_ssl_certificate_key)
bench_command.add_command(set_url_root)
bench_command.add_command(set_mariadb_host)
bench_command.add_command(set_default_site)
bench_command.add_command(download_translations)
bench_command.add_command(shell)
bench_command.add_command(backup_site)
bench_command.add_command(backup_all_sites)
bench_command.add_command(release)
bench_command.add_command(prepare_staging)
bench_command.add_command(renew_lets_encrypt)
bench_command.add_command(disable_production)
bench_command.add_command(bench_src)

from bench.commands.setup import setup
bench_command.add_command(setup)


from bench.commands.config import config
bench_command.add_command(config)

from bench.commands.git import remote_set_url, remote_reset_url, remote_urls
bench_command.add_command(remote_set_url)
bench_command.add_command(remote_reset_url)
bench_command.add_command(remote_urls)

from bench.commands.install import install
bench_command.add_command(install)

@contextlib.contextmanager
def tempchdir(dirpath, cleanup):
	basedir = os.getcwd()
	os.chdir(osp.expanduser(dirpath))
	try:
		yield
	finally:
		os.chdir(basedir)
		cleanup()

@contextlib.contextmanager
def tempdir():
	dirpath = tempfile.mkdtemp()
	def cleanup():
		shutil.rmtree(dirpath)
	with tempchdir(dirpath, cleanup):
		yield dirpath

@click.command('migrate-env')
@click.argument('python', type = click.Choice(['python2', 'python3']))
@click.option('--no-backup', default = False, help = 'Do not backup the existing Virtual Environment')
def migrate_env(python, no_backup = False):
	"""
	Migrate Virtual Environment to desired Python Version.
	"""

	python = which(python)

	path   = os.getcwd()
	# This is with the assumption that a bench is set-up within path.
	try:
		with tempdir() as dirpath:
			virtualenv = which('virtualenv')
			
			nvenv      = 'env'
			pvenv      = osp.join(dirpath, nvenv)

			exec_cmd('{virtualenv} --python {python} {pvenv}'.format(
				virtualenv = virtualenv,
				python     = python,
				pvenv      = pvenv
			), cwd = dirpath)

			# TODO: Options

			papps  = osp.join(path, 'apps')
			for app in os.listdir(papps):
				papp = osp.join(papps, app)
				if osp.isdir(papp) and osp.exists(osp.join(papp, 'setup.py')):
					pip = osp.join(pvenv, 'bin', 'pip')
					exec_cmd('{pip} install -e {app}'.format(
						pip = pip, app = papp
					))

			# I know, bad name for a flag. Thanks, Ameya! :| - <achilles@frappe.io>
			if not no_backup:
				# Back, the f*ck up.
				parch = osp.join(path, 'archived_envs')
				if not osp.exists(parch):
					os.mkdir(parch)
				
				# Simply moving. Thanks, Ameya.
				# I'm keen to zip.
				source = osp.join(path, 'env')
				target = parch

				log.debug('Backing up Virtual Environment')
				stamp  = datetime.now().strftime('%Y%m%d_%H%M%S')
				dest   = osp.join(path, str(stamp))
				
				os.rename(source, dest)
				shutil.move(dest, target)
			
			log.debug('Setting up a New Virtual {python} Environment'.format(
				python = python
			))
			source = pvenv
			target = path

			shutil.move(source, target)
		
		log.debug('Migration Successful to {python}'.format(
			python = python
		))
	except:
		log.debug('Migration Error')
		raise

bench_command.add_command(migrate_env)