import re
import click
from collections import namedtuple
from . import absjoin, THIS_DIR, to_bool, run_command, is_dry_run

REV_COMMIT_MESSAGE = "[skip ci] rev version {old} -> {new}"
Version = namedtuple("Version", "find replace")

# The list of files that we need to update the version number.
FILES = {
    absjoin(THIS_DIR, "..", "pyproject.toml"): Version(
        find="version = ['\"](.*?)['\"]", replace='version = "{version}"'
    ),
    absjoin(THIS_DIR, "..", "yamicache", "__init__.py"): Version(
        find="__version__ = ['\"](.*?)['\"]", replace="__version__ = '{version}'"
    ),
}


def get_versions():
    """Return a list of the versions found"""
    versions = {}
    for fpath, version in FILES.items():
        with open(fpath) as fh:
            text = fh.read()

        match = re.search(version.find, text)
        if match:
            ver = match.group(1)
        else:
            click.echo("ERROR: Cant find match [%s] in [%s]" % (version.find, fpath))
            ver = None

        versions[fpath] = ver

    return versions


def show_versions():
    """Show versions"""
    versions = get_versions()

    for fpath, ver in versions.items():
        click.echo("%s: %s" % (fpath, ver))

    # It's a serious issue if any version is mismatched
    if len(set(versions.values())) != 1:
        click.echo("ERROR: Version mismatch: %s" % versions.values())
        raise click.Abort()


def rev_version():
    """Update versions"""
    old_version = list(get_versions().values())[0]
    dry_run = is_dry_run()

    # Increase the minor part by 1
    major, minor, rest = old_version.split(".", 2)
    if minor.isdigit():
        minor = int(minor) + 1

    new_ver = "%s.%s.0" % (major, minor)

    click.echo("Old version is [%s]." % old_version)
    value = click.prompt("New version is [%s].  OK?" % new_ver)
    while not to_bool(value):
        new_ver = click.prompt("Enter new version: ")
        value = click.prompt("New version is [%s].  OK?" % new_ver)

    dry_run = is_dry_run()
    click.echo("dry run: %s" % dry_run)
    click.echo("old ver: %s" % old_version)
    click.echo("new ver: %s" % new_ver)
    click.confirm("OK to continue?", abort=True)

    files_modified = []
    for fpath, version in FILES.items():
        with open(fpath) as fh:
            text = fh.read()

        match = re.search(version.find, text)
        if match:
            if not dry_run:
                text = re.sub(
                    match.group(0), version.replace.format(version=new_ver), text
                )
                with open(fpath, "wb") as fh:
                    fh.write(text)
                click.echo("updated %s" % fpath)
            else:
                click.echo("would have updated %s" % fpath)
            files_modified.append(fpath)
        else:
            click.echo("ERROR: Cant find match [%s] in [%s]" % (version.find, fpath))

    return files_modified


def tag_version():
    """Tag this version"""
    current_version = list(get_versions().values())[0]
    new_tag = "v%s" % current_version

    (text, returncode) = run_command(["git", "tag", "-l", "--sort=-v:refname"])
    latest_tag = text.splitlines()[0]

    if latest_tag == new_tag:
        click.echo('ERROR: Tag "%s" already exists' % new_tag)
        raise click.Abort()

    click.echo("current version: %s" % current_version)
    click.echo("     latest tag: %s" % latest_tag)
    click.echo("        new tag: %s" % new_tag)

    click.confirm("OK to continue with tag creation?", abort=True)

    run_command(["git", "tag", "-a", new_tag, "-m", '"version %s"' % new_tag])
    run_command(["git", "push", "--follow-tags"])
