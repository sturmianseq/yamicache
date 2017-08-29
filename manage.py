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
import SocketServer
import SimpleHTTPServer
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

    if ('stderr' not in kwargs):
        kwargs['stderr'] = subprocess.STDOUT

    if ('shell' not in kwargs) and isinstance(args[0], basestring):
        kwargs['shell'] = True

    try:
        text = subprocess.check_output(*args, **kwargs)
        returncode = 0
    except subprocess.CalledProcessError as e:
        text = e.output
        returncode = e.returncode

    return (text, returncode)


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


def show_version():
    with open('yamicache/__init__.py') as fh:
        text = fh.read()

    match = re.search(
        '__version__\s+=\s+["\'](?P<version>[\d\.a-z]+)["\']', text)
    if match:
        click.echo('current source version: %s' % match.group('version'))

    (text, returncode) = run_command([
        'git', 'tag', '-l', '--sort=-version:refname'])
    if text:
        latest = text.split()[0]
        click.echo('current tag: %s' % latest)
    else:
        click.echo('no tags found')


def build_all():
    '''Build the distribution & docs'''
    build_dist()
    build_docs()


def build_dist():
    '''Build the distribution'''
    run_command(['rm', 'dist/*'])
    (text, returncode) = run_command([
        'python', 'setup.py', 'sdist', 'bdist_wheel'])


def build_docs():
    '''Build HTML documentation'''
    clean_docs()
    click.echo(run_command(['sphinx-apidoc', '-o', 'docs/', 'yamicache'])[0])
    click.echo(
        run_command(['make', 'html'], cwd='docs')[0]
    )


def serve_docs():
    '''Serve the HTML docs'''
    os.chdir('docs/_build/html')
    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(("", 8000), Handler)

    click.echo("serving at http://127.0.0.1:8000")
    httpd.serve_forever()


def clean_docs():
    '''Clean the HTML documentation'''
    run_command(['rm', '-rf', 'docs/_build/*'])
    run_command(['rm', 'docs/yamicache.rst'])
    run_command(['rm', 'docs/modules.rst'])


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
def add_command(name, f, group, description=None):
    group.add_command(click.Command(
        name, callback=f, help=description or f.__doc__))


cli = click.Group()
add_command('lint', lint, cli)
add_command('deploy', deploy, cli)
add_command('install', install, cli)
add_command('uninstall', uninstall, cli)

show_group = click.Group('show', help='Display project info')
add_command('version', show_version, show_group)
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
add_command('docs', clean_docs, docs_group)
add_command('serve', serve_docs, docs_group)
cli.add_command(docs_group)
###############################################################################


if __name__ == '__main__':
    cli()
