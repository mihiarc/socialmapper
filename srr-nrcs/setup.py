from setuptools import setup, find_packages

setup(
    name="srr_nrcs",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "geopandas",
        "matplotlib",
        "contextily",
        "overpy",
        "requests",
        "pyproj",
        "pyyaml"
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
            "flake8",
            "black"
        ]
    }
) 