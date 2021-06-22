#!/usr/bin/env python
import setuptools


def get_version(filename):
    with open(filename) as in_fh:
        for line in in_fh:
            if line.startswith('__version__'):
                return line.split('=')[1].strip()[1:-1]
    raise ValueError("Cannot extract version from %s" % filename)


setuptools.setup(
    name="tmuxpair",
    version=get_version("tmuxpair.py"),
    url="https://github.com/goerz/tmuxpair#tmuxpair",
    author="Michael Goerz",
    author_email="mail@michaelgoerz.net",
    description=(
        "Command line script for setting up a temporary tmux session for "
        "pair programming"
    ),
    install_requires=[
        'Click>=5',
        'sshkeys>=0.5',
    ],
    extras_require={'dev': ['pytest', 'coverage', 'pytest-cov']},
    py_modules=['tmuxpair'],
    entry_points='''
        [console_scripts]
        tmuxpair=tmuxpair:main
    ''',
    classifiers=[
        'Environment :: Console',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
