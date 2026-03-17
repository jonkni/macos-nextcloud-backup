from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="macos-nextcloud-backup",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Time Machine-like incremental backup solution for macOS to Nextcloud",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/YOUR_USERNAME/macos-nextcloud-backup",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: System :: Archiving :: Backup",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: MacOS :: MacOS X",
    ],
    python_requires=">=3.9",
    install_requires=[
        "click>=8.0.0",
        "pyyaml>=6.0",
        "webdavclient3>=3.14.6",
        "requests>=2.31.0",
        "sqlalchemy>=2.0.0",
        "keyring>=24.0.0",
        "colorama>=0.4.6",
        "tqdm>=4.66.0",
    ],
    entry_points={
        "console_scripts": [
            "mnb=mnb.cli.main:cli",
            "mnb-gui=mnb.gui.menubar:main",
        ],
    },
)
