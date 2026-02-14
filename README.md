# chartroom

[![PyPI](https://img.shields.io/pypi/v/chartroom.svg)](https://pypi.org/project/chartroom/)
[![Changelog](https://img.shields.io/github/v/release/simonw/chartroom?include_prereleases&label=changelog)](https://github.com/simonw/chartroom/releases)
[![Tests](https://github.com/simonw/chartroom/actions/workflows/test.yml/badge.svg)](https://github.com/simonw/chartroom/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/chartroom/blob/master/LICENSE)

CLI tool for creating charts

## Installation

Install this tool using `pip`:
```bash
pip install chartroom
```
## Usage

For help, run:
```bash
chartroom --help
```
You can also use:
```bash
python -m chartroom --help
```
## Development

To contribute to this tool, first checkout the code. Then create a new virtual environment:
```bash
cd chartroom
python -m venv venv
source venv/bin/activate
```
Now install the dependencies and test dependencies:
```bash
pip install -e '.[test]'
```
To run the tests:
```bash
python -m pytest
```
