from traceback import extract_stack
from setuptools import setup, find_packages

packages = find_packages()

print(packages)
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

version = "0.1"

setup(
    name="imcf_eda",
    version=version,
    description="Event-driven acquisition",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # url="https://github.com/wl-stepp/imcf_eda,
    # project_urls={
    #     "Bug Tracker": "https://github.com/wl-stepp/eda_plugin/issues",
    # },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    packages=packages,
    package_data={"": ["settings.json", "utility/*.jar", "utility/models/*"]},
    include_package_data=True,
    install_requires=[
        'useq-schema',
        'numpy',
        'pymmcore-plus',
    ],
    extras_require={
        'ilp': ['pulp'],
        'pyqt5': ['PyQt5'],
        'pyqt6': ['PyQt6'],
        'test': ['pytest', 'pytest-qt'],
        },
    author="Willi L. Stepp",
    author_email="willi.stepp@epfl.ch",
    python_requires=">=3.10",
)
