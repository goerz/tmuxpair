#!/usr/bin/env python
"""Command line script for setting up a temporary tmux session for pair
programming"""
# Copyright (C) 2016 Michael Goerz. See LICENSE for terms of use.

import logging
import sys
import os
import shutil
import contextlib
import signal
import subprocess as sp
from collections import OrderedDict
from copy import copy

import sshkeys
import click
from click import echo

__version__ = '1.1.0'


class AuthorizedKeys(object):
    """Representation of an authorized_keys file, consisting of a list of keys,
    with associated options (optionally)"""
    def __init__(self):
        self.keys = []

    def add_key(self, key):
        """Add a key (instance of sshkeys.Key)"""
        self.keys.append(key)

    def add_key_file(self, file, options=None):
        """Add the public key stored in the given file"""
        key = sshkeys.Key.from_pubkey_file(file)
        self.add_key(key)

    def extend(self, other):
        """Extend with keys and options of another AuthorizedKeys instance"""
        self.keys.extend(other.keys)

    def __len__(self):
        """Number of keys"""
        return len(self.keys)

    def __iter__(self):
        """Return iterator over keys"""
        return iter(self.keys)

    def __contains__(self, key):
        """Check whether the given key (instance of sshkeys.Key) is used
        (ignoring the options setting."""
        if isinstance(key, sshkeys.Key):
            for k in self.keys:
                if k.data == key.data:
                    return True
        else: # key is assumed to be the data directly
            for k in self.keys:
                if k.data == key:
                    return True
        return False

    @classmethod
    def read(cls, file):
        """Read an authorized_keys file"""
        authorized_keys = cls()
        with click.open_file(file) as in_fh:
            for line in in_fh:
                line = line.strip()
                if not line.startswith("#"):
                    key = sshkeys.Key.from_pubkey_line(line)
                    authorized_keys.add_key(key)
        return authorized_keys

    def __copy__(self):
        """Return copy of object"""
        new_copy = AuthorizedKeys()
        for key in self.keys:
            new_copy.add_key(key)
        return new_copy

    def __str__(self):
        """Content of an authorized_keys file, as a string"""
        return "\n".join([k.to_pubkey_line() for k in self.keys])

    def write(self, file):
        """Write an authorized_keys file"""
        with click.open_file(file, 'w') as out_fh:
            out_fh.write(str(self))


def _sigterm_handler(signum, frame):
    sys.exit(0)
_sigterm_handler.__enter_ctx__ = False


@contextlib.contextmanager
def handle_exit(callback=None, append=False):
    """A context manager which properly handles SIGTERM and SIGINT
    (KeyboardInterrupt) signals, registering a function which is
    guaranteed to be called after signals are received.
    Also, it makes sure to execute previously registered signal
    handlers as well (if any).

    If append == False raise RuntimeError if there's already a handler
    registered for SIGTERM, otherwise both new and old handlers are
    executed in this order.
    """
    # http://code.activestate.com/recipes/577997-handle-exit-context-manager/
    old_handler = signal.signal(signal.SIGTERM, _sigterm_handler)
    if (old_handler != signal.SIG_DFL) and (old_handler != _sigterm_handler):
        if not append:
            raise RuntimeError("there is already a handler registered for "
                               "SIGTERM: %r" % old_handler)

        def handler(signum, frame):
            try:
                _sigterm_handler(signum, frame)
            finally:
                old_handler(signum, frame)
        signal.signal(signal.SIGTERM, handler)

    if _sigterm_handler.__enter_ctx__:
        raise RuntimeError("can't use nested contexts")
    _sigterm_handler.__enter_ctx__ = True

    try:
        yield
    except KeyboardInterrupt:
        pass
    except SystemExit as err:
        # code != 0 refers to an application error (e.g. explicit
        # sys.exit('some error') call).
        # We don't want that to pass silently.
        # Nevertheless, the 'finally' clause below will always
        # be executed.
        if err.code != 0:
            raise
    finally:
        _sigterm_handler.__enter_ctx__ = False
        if callback is not None:
            callback()


@click.command()
@click.help_option('-h', '--help')
@click.version_option(version=__version__)
@click.option('--authorized_keys',
        default=os.path.expanduser('~/.ssh/authorized_keys'),
        show_default=True,
        help='authorized_keys file to temporarily modify.',
        type=click.Path(exists=True, dir_okay=False))
@click.option('--session', '-s', default='pair', show_default=True,
        metavar='SESSION_NAME', help="Name of tmux session to use.")
@click.option('--read-only', '-r', is_flag=True, default=False,
        help='Allow read-only access only for remote users.')
@click.option('--tmux', default='tmux', metavar='TMUX', show_default=True,
        help='Executable to be used for tmux')
@click.option('--allow-port-forwarding', is_flag=True, default=False,
        help='Allow remote user to forward ports.')
@click.option('--debug', is_flag=True,
    help='enable debug logging')
@click.argument('keys', nargs=-1, type=click.Path(exists=True, dir_okay=False),
        required=True)
def main(authorized_keys, keys, session, read_only, tmux, allow_port_forwarding, debug):
    """Run a new tmux session, or attach to an existing tmux session, for pair
    programming.

    Each file given as KEYS may contain an arbitrary number of public SSH keys.
    These keys are temporarily added to the SSH authorized_keys file. Any user
    connecting via SSH with a matching key will automatically be attached to
    the tmux session.

    When the tmux session ends or is detached, the original authorized_keys
    file will be restored. Also, any remote connections are immediately
    severed. This ensures that at no point, the remote user has unsupervised
    access to the system. Any interaction besides through the tmux session is
    forbidden. Port forwarding or use of scp is forbidden.
    """
    logging.basicConfig(level=logging.WARNING)
    logger = logging.getLogger(__name__)
    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Enabled debug output")

    authorized_keys = os.path.expanduser(authorized_keys)
    authorized_keys_backup = authorized_keys+'.tmuxpair_bak'
    if os.path.isfile(authorized_keys_backup):
        click.echo("Error: Backup file %s already exists. This means that "
                   "either an instance of this script is already running, or "
                   "an earlier instance has crashed." % authorized_keys_backup,
                   err=True)
        sys.exit(1)
    shutil.copy(authorized_keys, authorized_keys_backup)
    def cleanup():
        click.echo("Cleaning up, restoring %s..." % authorized_keys)
        shutil.move(authorized_keys_backup, authorized_keys)
        try:
            sp.check_output([tmux, 'detach-client', '-s', session],
                            stderr=sp.STDOUT)
            click.echo("all remote clients have been disconnected...")
        except sp.CalledProcessError:
            pass # Usually, this is because the session did no longer exist
        click.echo("Done.")
    with handle_exit(callback=cleanup):
        authorized_data = AuthorizedKeys.read(authorized_keys)
        if read_only:
            connect_cmd = '{tmux} attach -r -t {session}'.format(
                        tmux=tmux, session=session)
        else:
            connect_cmd = '{tmux} attach -t {session}'.format(
                        tmux=tmux, session=session)
        for file in keys:
            keys_data = AuthorizedKeys.read(file)
            for key in keys_data:
                key.options = OrderedDict([
                    ('command', connect_cmd),
                    ])
                if not allow_port_forwarding:
                    key.options['no-port-forwarding'] = True
            authorized_data.extend(keys_data)
        authorized_data.write(authorized_keys)
        try:
            sp.check_output([tmux, 'attach', '-t', session], stderr=sp.STDOUT)
        except sp.CalledProcessError:
            try:
                sp.check_output([tmux, 'new-session', '-s', session],
                                 stderr=sp.STDOUT)
            except sp.CalledProcessError as e:
                click.echo("Error: Cannot start tmux: %s" % e.output, err=True)
                sys.exit(1)

