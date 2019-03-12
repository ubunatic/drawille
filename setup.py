import sys
from setuptools import setup, find_packages

if sys.version_info.major < 3:
    extra_requires = ['future', 'backports.shutil_get_terminal_size']
else:
    extra_requires = []

setup(
    name = 'drawille',
    version = '0.2.0',
    author = 'Adam Tauber',
    author_email = 'asciimoo@gmail.com',
    description = ('Drawing in terminal with unicode braille characters'),
    license = 'AGPLv3+',
    keywords = "terminal braille drawing canvas console repl",
    url = 'https://github.com/asciimoo/drawille',
    scripts = [],
    packages = find_packages(
        exclude = ['contrib', 'docs', 'tests'],
    ),
    install_requires = [
        'pygments<3.0.0',
        'prompt-toolkit<2.0.0',
    ] + extra_requires,
    download_url = 'https://github.com/asciimoo/drawille/tarball/master',
    entry_points={
        "console_scripts": [
            "drawille=drawille:main",
            "turtille=drawille:main",
        ]
    },
    classifiers = [
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        'Environment :: Console',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
