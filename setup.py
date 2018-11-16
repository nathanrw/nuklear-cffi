"""
Setup script for 'pynk' library.
"""

from setuptools import setup

# Note: installing pcpp from github and not pypi
# because we depend on PR #7 which has not (as of
# writing) been merged.
#
# See https://github.com/ned14/pcpp/pull/7

setup(name='pynk',
      version='0.3',
      description='Python integration of the \'nuklear\' C library.',
      url='http://github.com/nathanrw/nuklear-cffi',
      author='Nathan Woodward',
      author_email='nathanrichardwoodward@gmail.com',
      license='Public domain',
      packages=['pynk'],
      setup_requires=["cffi>=1.0.0", "ply", "pcpp==1.0.1"],
      cffi_modules=["pynk/build.py:maker"],
      install_requires=["cffi>=1.0.0"],
      dependency_links=["http://github.com/nathanrw/pcpp/tarball/master#egg=pcpp-1.0.1"],
      zip_safe=False)
