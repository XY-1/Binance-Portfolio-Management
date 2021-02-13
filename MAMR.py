from data.candles import candleLoader
from portfolioManagement.portfolioManagement import PAMRPortfolioManager, MAMRPortfolioManager
import datetime
from matplotlib import pyplot as plt

import numpy as np

#need to run data/get_candles_spot.py
DATABASE = 'data/candles_12h.db'
#CURRENCIES = ['BTC', 'ETH', 'EOS', 'LTC', 'BNB', 'XRP', 'BCH', 'ADA', 'XMR']
#CURRENCIES = ['BTC', 'ETH', 'EOS', 'LTC', 'BNB', 'BCH', 'ADA']
CURRENCIES = ['ETH', 'EOS', 'FTT', 'LTC', 'BCH', 'ADA', 'XRP', 'XMR', 'LSK', 'FCT', 'XEM', 'MONA', 'XLM', 'QTMU', 'BAT', 'IOST', 'ENJ', 'DOGE', 'DOT', 'LINK', 'ATOM', 'TRX', 'IOTA' ,'VET', 'XTZ', 'THETA', 'NEO', 'FTT', 'MKR', 'DASH', 'ETC', 'ZRX', 'DCR', 'ZIL', 'WAVES' ,'SC', 'AE', 'MANA','NANO','ONT','ZEC','DGB','OMG','HBAR','ICX','ZEN','KNC','BNT','RVN','OCEAN','MATIC']

#Quote Assets
QUOTES = ['BTC', 'BNB']
RISKLESS = 'USDT'


DATABASE = 'data/candles_12h.db'

class binanceBot:
	def __init__(self, api, secret, saved=None, n=26):
		self.account = account(api, secret)
		self.balances = np.array([self.account.balances[c] if c in self.account.balances else 0.0 for c in [RISKLESS] + QUOTES + CURRENCIES])

		

		if saved is not None:
			try:
				with open(saved, 'rb') as file:
					loaded = pickle.load(file)
					self.manager = loaded.manager
					self.prices = loaded.prices
					self.returns = loaded.returns
					self.update_times = loaded.update_times
					self.portfolio = np.array(loaded.portfolio)
					return

			except FileNotFoundError:
				pass

		#get the portfolio...
		self.manager = MAMRPortfolioManager(len(CURRENCIES) + len(QUOTES) + 1, 4.105, 9.5, 1000, 0.0, n)
		

		from data.get_candles_spot import main as get_candles
		get_candles()

		

		price_changes = []
		times = []
		self.prices = []
		
		for candle in candleLoader(DATABASE):
			#consider markets trading against BTC, so we need to invert the USDT price
			self.prices.append(np.array([1] + [candle[currency + 'USDT_OPEN'] for currency in QUOTES + CURRENCIES]))
			if len(self.prices) == 1:
				continue
			else:
				price_changes.append(self.prices[-1] / self.prices[-2])
				times.append(candle['open_time'])

		for change, time in zip(price_changes[-n:], times[-n:]):
			self.manager.update(time, change)


		self.returns = price_changes
		self.update_times = times
		self.portfolio = self.account.get_portfolio_weighted(['USDT'] + QUOTES + CURRENCIES)
		
		self.manager.portfolio = np.array(self.portfolio)
		self.prices.append(np.array([1.05 ** (0.5 / 365)] + [np.mean(market.prices([a + 'USDT' for a in QUOTES + CURRENCIES])[b + 'USDT']) for b in QUOTES + CURRENCIES]))

	def save(self, location):
		with open(location, 'wb') as file:
			pickle.dump(self, file)

	def update(self):
		market_prices =market.prices([a + 'USDT' for a in QUOTES + CURRENCIES])
		#self.prices.append(np.array([1.05 ** (0.5 / 365)] + [np.mean(market_prices[b + 'USDT']) for b in QUOTES + CURRENCIES]))
		self.prices.append(np.array([1] + [np.mean(market_prices[b + 'USDT']) for b in QUOTES + CURRENCIES]))
		returns = self.prices[-1] / self.prices[-2]
		returns[0] = 1.05 ** (0.5 / 365) #should get realtime returns

		self.returns.append(returns)
		self.update_times.append(int(datetime.datetime.now().timestamp() * 1000))
		usd_balances = self.balances * self.prices[-1]

		self.manager.update(self.update_times[-1], self.returns[-1])

		
		target_portfolio = np.array(self.manager.portfolio)
		#swutch bnb abd usdt to get fee reductions
		usdt_proportion = target_portfolio[0]
		target_portfolio[0] = target_portfolio[2]
		target_portfolio[2] = usdt_proportion
		
		#The prices in BNB will be aquired in the trade method, maybe should just get these originally... 
		self.account.trade_to_portfolio('BNB', ['BNB', 'BTC', 'USDT'], CURRENCIES, target_portfolio)


		self.portfolio = self.account.get_portfolio_weighted(['USDT'] + QUOTES + CURRENCIES)
		print(self.portfolio, self.manager.portfolio)
		
		with open('output.txt', 'a') as file:
			file.write(str(self.manager.portfolio) + str(self.portfolio))


def main():


	try:
		import keys
	except ModuleNotFoundError:
		print('keys.py file missing - see readme for set up instructions')
		return 

	bot = binanceBot(keys.API, keys.SECRET, 'state.pkl')
	
	bot.update()
	bot.save('state.pkl')

if __name__ == '__main__':
	main()

def main():
	#get all the candles and calculate the price changes
	price_changes = []
	prices = []
	times = []

	for candle in candleLoader(DATABASE):
		#consider markets trading against BTC, so we need to invert the USDT price
		prices.append(np.array([1] + [candle[currency + 'USDT_OPEN'] for currency in CURRENCIES]))
		if len(prices) == 1:
			continue
		else:
			price_changes.append(prices[-1] / prices[-2])
			price_changes[-1][0] = 1.05 ** (0.5 / 365)
			times.append(candle['open_time'])

	#manager = MAMRPortfolioManager(len(CURRENCIES) + 1, 11.75, 371, 995, 0.001, 23)
	#manager = MAMRPortfolioManager(len(CURRENCIES) + 1, 4.105, 9.5, 1000, 0.00075, 26)
	manager = MAMRPortfolioManager(len(CURRENCIES) + 1, 4.105, 9.5, 1000, 0.000, 26)
	#manager = MAMRPortfolioManager(len(CURRENCIES) + 1, 50, 50, 60, 0.000, 26)

	for change, time in zip(price_changes, times):
		manager.update(time, change)


	print(manager.value)
	
	
	plt.figure(0)



	plt.plot([datetime.datetime.fromtimestamp(time / 1000) for time in times], np.array(manager.values[1:]), label='MAMR Portfolio Value')
	plt.plot([datetime.datetime.fromtimestamp(time / 1000) for time in times], [p[1]/prices[0][1] for p in prices[1:]], label='BTC Return')
	plt.yscale('log')
	plt.ylabel('Return')
	plt.title('MAMR 12 hour updates, 0.001 Transaction Fee')
	plt.legend()


	plt.figure(1)

	for i, currency in enumerate(['USDT'] + CURRENCIES):
		plt.plot([datetime.datetime.fromtimestamp(time / 1000) for time in times], [p[i] for p in manager.portfolios[1:]], label=currency)
	plt.legend()

	plt.show()

	


if __name__ == '__main__':
	main()
