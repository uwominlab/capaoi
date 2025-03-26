#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
`pip install .`
"""

from setuptools import setup, find_packages


with open("requirements.txt", mode="r", encoding="utf-8") as f:
    requirements: list[str] = [
        line.strip()
        for line in f
        if line.strip() and not line.startswith("#")
    ]


setup(
    name="capaoi",
    version="1.0.0",
    author="Dr. Xia Min, Dr. Rui Liu, Xuhua Huang and al.",
    author_email="rliu737@uwo.ca, xhuan484@uwo.ca",
    description=(
        "An industrial Automatic Optical Inspection project for capsules"
        "led by the Machine Intelligence (MIN) Lab at the"
        "University of Western Ontario."
    ),
    long_description=open("README.md", encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/uwominlab/capaoi",
    roject_urls={
        "Documentation": "https://github.com/uwominlab/capaoi/doc",
        "Source Code": "https://github.com/uwominlab/capaoi",
    },
    license="MIT",
    classifiers=[
        "Development Status :: 0 - Development/Alpha",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Topic :: Education :: Computer Vision",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords=[
        "computer vision",
        "industry 4.0",
        "university"
    ],
    python_requires=">=3.8",
    extras_require={
        "dev": ["pytest>=7.0", "black>=23.0"],
    },
    package_dir={"": "."},  # Root-level
    packages=find_packages(where="."),  # Automatically find packages in root
    py_modules=["main"],  # main.py
    install_requires=requirements,  # Pass the dependencies here
    entry_points={
        "console_scripts": [
            "capaoi=main:main",  # Maps the console command `capaoi` to `main` in `main.py`
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
