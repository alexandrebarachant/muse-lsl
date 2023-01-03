from setuptools import setup, find_packages
from shutil import copyfile
import os


def get_long_description():
    this_directory = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(this_directory, 'README.md')) as f:
        long_description = f.read()
        return long_description


def copy_docs():
    docs_dir = "muselsl/docs"
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)

    copyfile("README.md", docs_dir + "/README.md")
    # copyfile('blinks.png', docs_dir + '/blinks.png')


copy_docs()
long_description = get_long_description()

setup(
    name="muselsl",
    version="2.2.2",
    description="Stream and visualize EEG data from the Muse headset.",
    keywords="muse lsl eeg ble neuroscience",
    url="https://github.com/alexandrebarachant/muse-lsl/",
    author="Alexandre Barachant",
    author_email="alexandre.barachant@gmail.com",
    license="BSD (3-clause)",
    entry_points={"console_scripts": ["muselsl=muselsl.__main__:main"]},
    packages=find_packages(),
    package_data={"muselsl": ["docs/README.md", "docs/examples/*"]},
    include_package_data=True,
    zip_safe=False,
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        "bitstring",
        "bleak>=0.18.0",
        "pygatt",
        "pandas",
        "scikit-learn",
        "numpy",
        "seaborn",
        "pexpect",
    ] +
    (["pylsl==1.10.5"] if os.sys.platform.startswith("linux") else ["pylsl"]),
    extras_require={"Viewer V2": ["mne", "vispy"]},
    classifiers=[
        # How mature is this project?  Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 4 - Beta",
        # Indicate who your project is intended for
        "Intended Audience :: Science/Research",
        "Topic :: Software Development",
        # Pick your license as you wish (should match "license" above)
        "License :: OSI Approved :: BSD License",
        # Specify the Python versions you support here.  In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Operating System :: MacOS",
        "Programming Language :: Python",
    ],
)
