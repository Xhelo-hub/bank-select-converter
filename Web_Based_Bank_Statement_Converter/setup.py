#!/usr/bin/env python3
"""
Setup configuration for Web-Based Bank Statement Converter API
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r") as req:
        return [line.strip() for line in req if line.strip() and not line.startswith("#")]

setup(
    name="web-based-bank-statement-converter",
    version="1.0.0",
    author="Xhelo-hub",
    author_email="xhelo.palushi@konsulence.al",
    description="Web-based API for converting Albanian bank statements to QuickBooks format",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/Xhelo-hub/web-based-bank-statement-converter",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Accounting",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-flask>=1.2.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.950",
        ],
        "prod": [
            "gunicorn>=20.1.0",
            "nginx>=1.18.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "bank-converter-api=app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["templates/*.html", "static/*", "docs/*"],
    },
    keywords=[
        "albania", "bank", "statement", "converter", "quickbooks", 
        "api", "web", "flask", "accounting", "finance"
    ],
    project_urls={
        "Bug Reports": "https://github.com/Xhelo-hub/web-based-bank-statement-converter/issues",
        "Source": "https://github.com/Xhelo-hub/web-based-bank-statement-converter",
        "Documentation": "https://github.com/Xhelo-hub/web-based-bank-statement-converter/docs",
    },
)