# Kraken Portfolio Performance Parser

## Description

This Python project processes trades data and historical quotes from Kraken to generate reformatted records compatible with Portfolio Performance. It reads trade and historical data from CSV files, processes the data to calculate asset values and transaction details, and outputs the results to a new CSV file.

## Installation

1. **Install Poetry**: Follow the [Poetry Installation Guide](https://python-poetry.org/docs/#installation).

2. **Clone the Repository**:
3.
    ```sh
    git clone <repository_url>
    cd kraken-pp-parser
    ```

4. **Install Dependencies**:
    ```sh
    poetry install
    ```

This command will:
- Create a virtual environment.
- Install the required dependencies listed in `pyproject.toml`.

## Usage

To run the project, use:
```sh
poetry run python src/main.py
```
