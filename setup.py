from setuptools import setup, find_packages
setup(
    name = "btrsnap",
    version = "1.0.0",
    packages = find_packages(),
    entry_points = {
        'console_scripts': [
            'btrsnap = btrsnap.btrsnap:main',
        ]
    },

    
    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        '': ['*.txt', '*.rst'],
        # And include any *.msg files found in the 'hello' package, too:
    },

    # metadata for upload to PyPI
    author = "Mike Lenzen",
    author_email = "lenzenmi@example.com",
    description = "A program to simplify working with BTRFS snapshots.",
    license = "GPL3",
    keywords = "btrfs",
    url = "",   # project home page, if any
)