import os.path

from setuptools import setup


NAME = "pyvirtualdisplay"
PYPI_NAME = "PyVirtualDisplay"
URL = "https://github.com/ponty/pyvirtualdisplay"
DESCRIPTION = "python wrapper for Xvfb, Xephyr and Xvnc"
PACKAGES = [
    NAME,
    NAME + ".examples",
]

# get __version__
__version__ = None
exec(open(os.path.join(NAME, "about.py")).read())
VERSION = __version__

# extra = {}
# if sys.version_info >= (3,):
#     extra['use_2to3'] = True
#     extra['use_2to3_exclude_fixers'] = ['lib2to3.fixes.fix_import']

classifiers = [
    # Get more strings from
    # http://www.python.org/pypi?%3Aaction=list_classifiers
    "License :: OSI Approved :: BSD License",
    "Natural Language :: English",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
]

install_requires = ["EasyProcess>=0.3.0"]

setup(
    name=PYPI_NAME,
    version=VERSION,
    description=DESCRIPTION,
    # long_description=open("README.rst", "r").read(),
    classifiers=classifiers,
    keywords="Xvfb Xephyr X wrapper",
    author="ponty",
    # author_email='',
    url=URL,
    license="BSD",
    packages=PACKAGES,
    #     include_package_data=True,
    #     test_suite='nose.collector',
    #     zip_safe=False,
    install_requires=install_requires,
    # **extra
)
