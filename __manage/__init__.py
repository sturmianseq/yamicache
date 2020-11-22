import os
import click
import subprocess

THIS_DIR = os.path.abspath(os.path.dirname(__file__))


@click.pass_context
def is_dry_run(ctx):
    try:
        return ctx.parent.parent.params.get('dry_run', False)
    except:
        return True


def run_command(*args, **kwargs):
    '''
    Wrapper around `check_output` that will always return the text and
    return code, without raising an exception.
    '''
    if is_dry_run():
        cmd = '`' + ' '.join(*args) + '`, ' + ' '.join(['%s=%s' % (key, value) for (key, value) in kwargs.items()])
        click.echo('...would have ran: %s' % cmd)
        return ('--dry-run', 0)

    if 'stderr' in kwargs:
        kwargs.pop('stderr')

    if ('stderr' not in kwargs):
        kwargs['stderr'] = subprocess.STDOUT

    if ('shell' not in kwargs) and isinstance(args[0], str):
        kwargs['shell'] = True

    try:
        text = subprocess.check_output(*args, **kwargs)
        returncode = 0
    except subprocess.CalledProcessError as e:
        text = e.output
        returncode = e.returncode

    return (text, returncode)


def absjoin(*args):
    '''Return the absolute path to the joined arguments.'''
    return os.path.abspath(os.path.join(*args))


def to_bool(value):
    '''Try to convert the string to a boolean'''
    return value.lower()[0] in ['y', 't', '1'] if isinstance(value, str) else bool(value)
