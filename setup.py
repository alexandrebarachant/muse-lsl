from setuptools import setup, find_packages
from shutil import copyfile
import os

def copy_docs():
    docs_dir = 'muselsl/docs'
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)

    copyfile('README.md', docs_dir + '/README.md')
    copyfile('blinks.png', docs_dir + '/blinks.png')

copy_docs()

setup(name='muse-lsl',
      version='1.0.0',
      description='Stream and visualize EEG data from the Muse 2016 headset.',
      keywords='muse lsl eeg ble neuroscience',
      url='https://github.com/alexandrebarachant/muse-lsl/',
      author='Alexandre Barachant',
      author_email='alexandre.barachant@gmail.com',
      license='BSD (3-clause)',
      scripts=['muselsl/muse-lsl.py'],
      packages=find_packages(),
      package_data={'muselsl': ['docs/blinks.png', 'docs/README.md']},
      include_package_data=True,
      zip_safe=False,
      install_requires=['bitstring', 'pylsl', 'pygatt', 'pandas', 'scikit-learn', 'numpy', 'seaborn', 'pexpect'],
      extra_requires=['mne'],
      classifiers=[
    # How mature is this project?  Common values are
    #   3 - Alpha
    #   4 - Beta
    #   5 - Production/Stable
    'Development Status :: 4 - Beta',

    # Indicate who your project is intended for
    'Intended Audience :: Science/Research',
    'Topic :: Software Development :: Utilities',

    # Pick your license as you wish (should match "license" above)
    'License :: OSI Approved :: BSD License',

    # Specify the Python versions you support here.  In particular, ensure
    # that you indicate whether you support Python 2, Python 3 or both.
    'Operating System :: Microsoft :: Windows',
    'Operating System :: POSIX',
    'Operating System :: Unix',
    'Operating System :: MacOS'

    'Programming Language :: Python']
    )
