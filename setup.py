"""
Setup script for 'pynk' library.
"""

from setuptools import setup

setup(name='pynk',
      version='0.1',
      description='Python integration of the \'nuklear\' C library.',
      url='http://github.com/nathanrw/nuklear-cffi',
      author='Nathan Woodward',
      author_email='nathanrichardwoodward@gmail.com',
      license='TODO',
      packages=['pynk'],
      setup_requires=["cffi>=1.0.0"],
      cffi_modules=["pynk/build.py:ffibuilder"],
      install_requires=["cffi>=1.0.0", "pcpp"],
      dependency_links=["git+ssh://git@github.com/nathanrw/pcpp.git#egg=pcpp"],
      zip_safe=False)
