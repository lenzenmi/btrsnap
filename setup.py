from setuptools import setup, find_packages
setup(
    name = "btrsnap",
    version = "1.1.1",
    packages = find_packages(exclude=["tests*"]),
    entry_points = {
        'console_scripts': [
            'btrsnap = btrsnap.btrsnap:main',
        ]
    },

    # metadata for upload to PyPI
    author = "Mike Lenzen",
    author_email = "lenzenmi@example.com",
    description = "A program to simplify working with BTRFS snapshots.",
    license = "GPL3",
    keywords = "btrfs",
    url = "",   # project home page, if any
)
