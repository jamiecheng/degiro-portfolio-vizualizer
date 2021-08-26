# DeGiro portfolio vizualizer
Retrievies the portfolio data over time using the transaction history. The script calculates the value of the portfolio for each day since the first transaction.

## Features
- Get the value of the porfolio over time
- Calculate the sharpe ratio (does not take account of deposits and withrawals)
- Get the correlation of the portfolio symbols

## Installation
Python 3 is required. Install the required packages in the commandline using
```
pip install -r requirements.txt
```

## Usage
Inside main.py an example is given. The script prompts for a username and password in the commandline. Never store these in a file.

Run the example with:
```
python main.py
```
