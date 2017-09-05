#!/usr/bin/env python2.7
# coding: utf-8
'''
This script is used to manage the `yamicache` project.
'''

# Imports #####################################################################
import os
import re
import click
import requests
# import subprocess
# import SocketServer
# import SimpleHTTPServer
from pkg_resources import parse_version
from __manage import run_command
from __manage.docs import serve_docs, build_docs, clean_docs
from __manage.version import show_versions, rev_version, tag_version


# Metadata ####################################################################
__author__ = 'Timothy McFadden'
__creationDate__ = '29-AUG-2017'
__license__ = 'MIT'


# Globals #####################################################################

def install():
    '''Install this package'''
    run_command(['pip', 'install', '-e', '.'])


def uninstall():
    '''Uninstall this package'''
    click.echo(run_command(['pip', 'uninstall', '-y', 'yamicache']))


def lint():
    '''Run flake8 against the project'''
    (text, returncode) = run_command([
        'flake8', '--ignore=E501', 'yamicache', 'tests'])

    if text:
        click.echo(text)
        click.echo('flake8 failed')
        raise click.Abort()

    click.echo('...linting passed')


def clean_build():
    '''Clean the build'''
    run_command(['rm', '-rf', 'yamicache.egg-info'])
    run_command(['rm', '-rf', 'build'])


def clean_dist():
    '''Clean the dist'''
    run_command(['rm', '-rf', 'dist/*'])


def clean_all():
    '''Clean all artifacts'''
    clean_build()
    clean_dist()
    clean_docs()


def build_all():
    '''Build the distribution & docs'''
    build_dist()
    build_docs()


def build_dist():
    '''Build the distribution'''
    run_command(['rm', 'dist/*'])
    (text, returncode) = run_command([
        'python', 'setup.py', 'sdist', 'bdist_wheel'])


def deploy():
    '''Upload dist to pypi'''
    (text, returncode) = run_command(['git', 'status', '--porcelain'])
    if text:
        click.echo("ERROR: You have non-commited changes:\n%s" % text)
        click.echo("...aborting deploy")
        raise click.Abort()

    if not os.path.exists('dist'):
        click.echo("'dist' directory does not exist; run `build` first.")
        raise click.Abort()

    # Get the version in dist
    tarball = next((
        x for x in os.listdir('dist')
        if (x.startswith('yamicache') and x.endswith('.tar.gz'))), None)

    if not tarball:
        click.echo(
            "Could not find tarball in `dist` directory; run `build` first.")
        raise click.Abort()

    match = re.search('yamicache-(?P<version>[\d\.a-z]+)\.tar\.gz', tarball)
    if not match:
        click.echo("Could not parse version from [%s]" % tarball)
    built_version = match.group('version')

    click.echo("found built version: %s" % built_version)
    built_version = parse_version(built_version)

    # check to see if the pypi version already exists
    try:
        package_json = requests.get(
            'https://pypi.python.org/pypi/yamicache/json')
        package_data = package_json.json()
        pypi_version = package_data['info']['version']
    except Exception as e:
        click.echo('Error getting version from pypi: %s' % e)
        raise click.Abort()

    click.echo('found pypi version: %s' % pypi_version)
    pypi_version = parse_version(pypi_version)

    if pypi_version >= built_version:
        click.echo('pypi version is >= built version; upload canceled')
        raise click.Abort()

    click.echo("...uploading")


# Create the CLI ##############################################################
def add_command(name, f, group, description=None, params=None):
    group.add_command(click.Command(
        name, callback=f, help=description or f.__doc__, params=params))


cli = click.Group()
cli.params.append(click.Option(('--dry-run',), is_flag=True, help="Don't actually execute anything"))
add_command('lint', lint, cli)
add_command('deploy', deploy, cli)
add_command('install', install, cli)
add_command('uninstall', uninstall, cli)

show_group = click.Group('show', help='Display project info')
add_command('version', show_versions, show_group)
cli.add_command(show_group)

build_group = click.Group('build', help='Build artifacts')
add_command('docs', build_docs, build_group, 'Build the docs')
add_command('dist', build_dist, build_group)
add_command('all', build_all, build_group)
cli.add_command(build_group)

clean_group = click.Group('clean', help="Remove artifacts")
add_command('docs', clean_docs, clean_group)
add_command('dist', clean_dist, clean_group)
add_command('all', clean_all, clean_group)
cli.add_command(clean_group)

docs_group = click.Group('docs', help="HTML Documentation")
add_command('build', build_docs, docs_group)
add_command('serve', serve_docs, docs_group)
add_command('clean', clean_docs, docs_group)
cli.add_command(docs_group)

ver_group = click.Group('ver', help="Version control")
add_command('show', show_versions, ver_group)
add_command('rev', rev_version, ver_group)
add_command('tag', tag_version, ver_group)
cli.add_command(ver_group)
###############################################################################


if __name__ == '__main__':
    cli()
