from setuptools import setup, find_packages

setup(name='muse-lsl',
      version='1.0.0',
      description='Stream and visualize EEG data from the Muse 2016 headset',
      keywords='muse lsl eeg ble neuroscience',
      url='',
      author='Alexandre Barachant',
      author_email='alexandre.barachant@gmail.com',
      license='BSD (3-clause)',
      packages=find_packages(),
      install_requires=['bitstring', 'pylsl', 'pygatt', 'psychopy', 'scikit-learn', 'pandas', 'numpy', 'mne', 'seaborn', 'pexpect'],
      zip_safe=False,
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
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.2',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',]
    ,)
