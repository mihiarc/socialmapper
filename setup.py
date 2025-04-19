#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="poi_query",
    version="0.1.0",
    description="Query OpenStreetMap POIs using Overpass API",
    author="Community Mapper",
    packages=find_packages(),
    install_requires=[
        "overpy",
        "pyyaml",
    ],
    entry_points={
        "console_scripts": [
            "poi-query=poi_query.query:main",
        ],
    },
    python_requires=">=3.6",
) 