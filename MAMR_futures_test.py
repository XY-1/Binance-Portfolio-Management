from data.candles import candleLoader
from portfolioManagement.portfolioManagement import MAMRPortfolioManager
import datetime
from matplotlib import pyplot as plt

import numpy as np

DATABASE = 'data/futures_candles_30m.db'
#CURRENCIES = ['BTC', 'ETH', 'EOS', 'LTC', 'BNB', 'XRP', 'BCH', 'ADA', 'XMR']
CURRENCIES = ['ETH', 'EOS', 'FTT', 'LTC', 'BCH', 'ADA', 'XRP', 'LSK', 'FCT', 'XEM', 'MONA', 'XLM', 'QTMU', 'BAT', 'IOST', 'ENJ', 'DOGE', 'DOT', 'LINK', 'ATOM', 'TRX', 'IOTA' ,'VET', 'XTZ', 'THETA', 'NEO', 'FTT', 'MKR', 'DASH', 'ETC', 'ZRX', 'DCR', 'ZIL', 'WAVES' ,'SC', 'AE', 'MANA','NANO','ONT','ZEC','DGB','OMG','HBAR','ICX','ZEN','KNC','BNT','RVN','OCEAN','MATIC']

def main():
	#get all the candles and calculate the price changes
	price_changes = []
	prices = []
	times = []
	funding_rates = []

	for candle in candleLoader(DATABASE):
		funding_rates.append([candle[currency + 'USDT_funding_rate'] for currency in CURRENCIES])
		prices.append(np.array([candle[currency + 'USDT_open'] for currency in CURRENCIES]))
		if len(prices) == 1:
			continue
		else:
			price_changes.append(prices[-1] / prices[-2])
			times.append(candle['open_time'])
	#self, n, epsilon, c_1, c_2, trading_fee=0, margin=1, omega=5
	manager = MAMRPortfolioManager(len(CURRENCIES), 1, 0.3, 10, 0.0000, 1, 10)
	for i, (change, time, funding_rate) in enumerate(zip(price_changes, times, funding_rates)):
		print((times[-1] - time) / (1000 * 60 * 30))
		
		if i % 16 == 0:		
			manager.update(time, change, np.array(funding_rate))
			#manager.update(time, change, np.zeros(len(CURRENCIES)))
			
		else:
			manager.update(time, change, np.zeros(len(CURRENCIES)))
	plt.figure(0)

	plt.plot([datetime.datetime.fromtimestamp(time / 1000) for time in times], manager.values[1:])
	plt.plot([datetime.datetime.fromtimestamp(time / 1000) for time in times], [p[1]/prices[0][1] for p in prices[1:]])
	plt.yscale('log')
	plt.figure(1)

	for i, currency in enumerate(CURRENCIES):
		plt.plot([p[i] for p in manager.portfolios], label=currency)
	plt.legend()

	plt.show()


if __name__ == '__main__':
	main()
