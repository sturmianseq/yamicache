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
import subprocess
from pkg_resources import parse_version


# Metadata ####################################################################
__author__ = 'Timothy McFadden'
__creationDate__ = '29-AUG-2017'
__license__ = 'MIT'


# Globals #####################################################################
def run_command(*args, **kwargs):
    '''
    Wrapper around `check_output` that will always return the text and
    return code, without raising an exception.
    '''

    if 'stderr' in kwargs:
        kwargs.pop('stderr')

    kwargs['stderr'] = subprocess.STDOUT

    try:
        text = subprocess.check_output(*args, **kwargs)
        returncode = 0
    except subprocess.CalledProcessError as e:
        text = e.output
        returncode = e.returncode

    return (text, returncode)


@click.group()
def cli():
    pass


@cli.group()
def show():
    pass


@show.command('version')
def show_version():
    with open('yamicache/__init__.py') as fh:
        text = fh.read()

    match = re.search('__version__\s+=\s+["\'](?P<version>[\d\.a-z]+)["\']', text)
    if match:
        click.echo('current source version: %s' % match.group('version'))

    (text, returncode) = run_command(['git', 'tag', '-l', '--sort=-version:refname'])
    if text:
        latest = text.split()[0]
        click.echo('current tag: %s' % latest)
    else:
        click.echo('no tags found')


@cli.command()
def build():
    run_command(r'rm dist/*', shell=True)
    (text, returncode) = run_command(['python', 'setup.py', 'sdist', 'bdist_wheel'])


@cli.command()
def deploy():
    (text, returncode) = run_command(['git', 'status', '--porcelain'])
    if text:
        click.echo("ERROR: You have non-commited changes:\n%s" % text)
        click.echo("...aborting deploy")
        raise click.Abort()

    if not os.path.exists('dist'):
        click.echo("'dist' directory does not exist; run `build` first.")
        raise click.Abort()

    # Get the version in dist
    tarball = next((x for x in os.listdir('dist') if (x.startswith('yamicache') and x.endswith('.tar.gz'))), None)
    if not tarball:
        click.echo("Could not find tarball in `dist` directory; run `build` first.")
        raise click.Abort()

    match = re.search('yamicache-(?P<version>[\d\.a-z]+)\.tar\.gz', tarball)
    if not match:
        click.echo("Could not parse version from [%s]" % tarball)
    built_version = match.group('version')

    click.echo("found built version: %s" % built_version)
    built_version = parse_version(built_version)

    # check to see if the pypi version already exists
    try:
        package_json = requests.get('https://pypi.python.org/pypi/yamicache/json')
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


if __name__ == '__main__':
    cli()
