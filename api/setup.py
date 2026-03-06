import os,sys
from optparse import OptionParser
from setuptools import find_packages, setup


def main():

    setup(
        name="bmkb",
        version="1.0",
        packages=find_packages(),
        include_package_data=True,
        zip_safe=False,
        install_requires=[
            'flask',
        ],
    )



if __name__ == '__main__':
    main()

