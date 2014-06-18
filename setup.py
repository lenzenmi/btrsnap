from distutils.core import setup

setup(
    name = "btrsnap",
    version = "2.0.0",
    packages = ['btrsnap'],
    scripts = ['scripts/btrsnap'],
    
    # metadata for upload to PyPI
    author = "Mike Lenzen",
    author_email = "lenzenmi@gmail.com",
    description = "A program to simplify working with BTRFS snapshots.",
    license = "GPL3",
    keywords = "btrfs",
    url = "",   # project home page, if any
)
