"""
Script to try and optimise the parameters for the PAMR Algorithm

The script brute forces around possible parameter values before refining the selection using the minimize function


Author: Alfred Holmes, https://github.com/alfredholmes
"""

import PAMR
from scipy.optimize import minimize
import numpy as np
import datetime

from multiprocessing import Pool

DATABASE = 'data/candles_30m.db'



def PAMR_mean_return(epsilon, c, price_changes):
	#initial_portfolio = np.ones(len(price_changes[0])) / len(price_changes[0])
	initial_portfolio = np.zeros(len(price_changes[0]))
	initial_portfolio[0] = 1
	portfolio = PAMR.PAMR(initial_portfolio, epsilon, c, 0.001)
	values, _, returns, _ = portfolio.run(price_changes)
	
	daily_returns = np.array(values[int(24):]) / np.array(values[:-int(24)])

	daily_returns = [d for i, d in enumerate(daily_returns) if i % 24 == 0] 
	

	print(epsilon, c, np.mean(daily_returns), np.sqrt(np.var(daily_returns)))

	return np.mean(returns)

def main():
	price_changes = PAMR.get_prices(DATABASE, datetime.datetime(year=2019, month=1, day=1).timestamp() * 1000, datetime.datetime(year=2020, month=1, day=1).timestamp() * 1000) 
	#price_changes = PAMR.get_prices(DATABASE) 
	
	epsilon_range = (0, 1)
	c_range = (0, 25)


	parameters = [(x, y, price_changes) for x in np.linspace(epsilon_range[0], epsilon_range[1], 25) for y in np.linspace(c_range[0], c_range[1], 25)]
	with Pool() as p:
		results = p.starmap(PAMR_mean_return, parameters)

	initial = results.index(max(results))
	print(parameters[initial][:2])
	result = minimize(lambda x: -PAMR_mean_return(x[0], x[1], price_changes), parameters[initial][:2])

	print(result)

if __name__ == '__main__':
	main()