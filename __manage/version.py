import re
import click
from collections import namedtuple
from . import absjoin, THIS_DIR, to_bool, run_command, is_dry_run

REV_COMMIT_MESSAGE = '[skip ci] rev version {old} -> {new}'
Version = namedtuple('Version', 'find replace')

# The list of files that we need to update the version number.
FILES = {
    absjoin(THIS_DIR, '..', 'setup.py'): Version(
        find="version=['\"](.*?)['\"]",
        replace="version='{version}'"
    ),
    absjoin(THIS_DIR, '..', 'yamicache', '__init__.py'): Version(
        find="__version__ = ['\"](.*?)['\"]",
        replace="__version__ = '{version}'"
    )
}


def get_versions():
    '''Return a list of the versions found'''
    versions = {}
    for fpath, version in FILES.items():
        with open(fpath) as fh:
            text = fh.read()

        match = re.search(version.find, text)
        if match:
            ver = match.group(1)
        else:
            click.echo('ERROR: Cant find match [%s] in [%s]' % (version.find, fpath))
            ver = None

        versions[fpath] = ver

    return versions


def show_versions():
    '''Show versions'''
    versions = get_versions()

    for fpath, ver in versions.items():
        click.echo('%s: %s' % (fpath, ver))

    # It's a serious issue if any version is mismatched
    if len(set(versions.values())) != 1:
        click.echo('ERROR: Version mismatch: %s' % versions.values())
        raise click.Abort()


def rev_version():
    '''Update versions'''
    old_version = get_versions().values()[0]
    dry_run = is_dry_run()

    # Increase the minor part by 1
    major, minor, rest = old_version.split('.', 2)
    if minor.isdigit():
        minor = int(minor) + 1

    new_ver = '%s.%s.0' % (major, minor)

    click.echo('Old version is [%s].' % old_version)
    value = click.prompt('New version is [%s].  OK?' % new_ver)
    while not to_bool(value):
        new_ver = click.prompt('Enter new version: ')
        value = click.prompt('New version is [%s].  OK?' % new_ver)

    do_commit = to_bool(click.prompt('Commit the change? '))
    do_tag = False
    do_push = False

    if do_commit:
        do_tag = to_bool(click.prompt('Create tag "v%s"? ' % new_ver))
        do_push = to_bool(click.prompt('Push the new version files? '))

    dry_run = is_dry_run()
    click.echo("dry run: %s" % dry_run)
    click.echo("old ver: %s" % old_version)
    click.echo("new ver: %s" % new_ver)
    click.echo(" commit: %s" % ('yes' if do_commit else 'no'))
    click.echo("    tag: %s" % ('yes' if do_tag else 'no'))
    click.echo("   push: %s" % ('yes' if do_push else 'no'))
    click.confirm("OK to continue?", abort=True)

    files_modified = []
    for fpath, version in FILES.items():
        with open(fpath) as fh:
            text = fh.read()

        match = re.search(version.find, text)
        if match:
            if not dry_run:
                text = re.sub(match.group(0), version.replace.format(version=new_ver), text)
                with open(fpath, 'wb') as fh:
                    fh.write(text)
                click.echo('updated %s' % fpath)
            else:
                click.echo('would have updated %s' % fpath)
            files_modified.append(fpath)
        else:
            click.echo('ERROR: Cant find match [%s] in [%s]' % (version.find, fpath))

    if do_commit:
        for fpath in files_modified:
            run_command(['git', 'add', fpath])

        message = REV_COMMIT_MESSAGE.format(old=old_version, new=new_ver)
        run_command(['git', 'commit', '-m"%s"' % message])

        if do_tag:
            run_command(['git', 'tag', '-a', 'v%s' % new_ver, '-m"version %s"' % new_ver])

        if do_push:
            run_command(['git', 'push', '--follow-tags'])
