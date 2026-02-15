#!/usr/bin/env python3
"""Setup script for LogLens."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="loglens",
    version="1.1.0",
    author="Nirakar",
    author_email="jenanirakar60@gmail.com",
    description="Linux log viewer with interactive Terminal UI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nirakar24/loglens",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Logging",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.10",
    install_requires=[
        "textual>=0.50.0",
    ],
    entry_points={
        "console_scripts": [
            "logtui=logtui:main",
        ],
    },
    package_data={
        "loglens.tui": ["*.css"],
    },
    include_package_data=True,
)
