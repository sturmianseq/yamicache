# https://gist.github.com/delijati/1690403
import os
import time
import click
import logging
import subprocess
import selenium.webdriver

from urllib import pathname2url
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from . import run_command, absjoin


MAKE_COMMAND = ['make', 'html']


class SphinxEventHandler(PatternMatchingEventHandler):
    """Rebuild and refresh on every change event."""

    def __init__(
        self, patterns=None, ignore_patterns=None,
        ignore_directories=False, case_sensitive=False
    ):
        super(SphinxEventHandler, self).__init__(
            patterns, ignore_patterns, ignore_directories, case_sensitive)

        path = os.path.join('_build', 'html', 'index.html')
        url = 'file:///' + pathname2url(os.path.abspath(path))
        self.driver = selenium.webdriver.Chrome()
        self.driver.get(url)

    def cleanup(self):
        self.driver.quit()

    def _run(self):
        print('creating HTML docs')
        subprocess.call(MAKE_COMMAND)
        self.driver.refresh()
        logging.info("Rebuild and refreshed")

    def on_moved(self, event):
        super(SphinxEventHandler, self).on_moved(event)
        self._run()

        what = 'directory' if event.is_directory else 'file'
        logging.info("Moved %s: from %s to %s", what, event.src_path,
                     event.dest_path)

    def on_created(self, event):
        super(SphinxEventHandler, self).on_created(event)
        self._run()

        what = 'directory' if event.is_directory else 'file'
        logging.info("Created %s: %s", what, event.src_path)

    def on_deleted(self, event):
        super(SphinxEventHandler, self).on_deleted(event)
        self._run()

        what = 'directory' if event.is_directory else 'file'
        logging.info("Deleted %s: %s", what, event.src_path)

    def on_modified(self, event):
        super(SphinxEventHandler, self).on_modified(event)
        self._run()

        what = 'directory' if event.is_directory else 'file'
        logging.info("Modified %s: %s", what, event.src_path)


def clean_docs():
    '''Clean the HTML documentation'''
    run_command(['rm', '-rf', 'docs/_build/*'])
    run_command(['rm', 'docs/yamicache.rst'])
    run_command(['rm', 'docs/modules.rst'])


def build_docs():
    '''Build HTML documentation'''
    clean_docs()
    click.echo(
        run_command(['make', 'html'], cwd='docs')[0]
    )


def serve_docs():
    '''Serve the docs and watch for changes'''
    THIS_DIR = os.path.abspath(os.path.dirname(__file__))
    DOCS_PATH = absjoin(THIS_DIR, '..', 'docs')
    os.chdir(DOCS_PATH)

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    event_handler = SphinxEventHandler(
        patterns=['*.rst', '*.py'], ignore_patterns=['*.html'],
        ignore_directories=["_build"])

    observer = Observer()
    observer.schedule(
        event_handler, path='.', recursive=True)
    observer.schedule(
        event_handler, path='..', recursive=False)
    observer.schedule(
        event_handler, path='../yamicache', recursive=True)

    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    event_handler.cleanup()
    observer.join()
