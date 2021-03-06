  class portfolioManager:
	#n number of assets available for investment, assets is an array  of names for each available assets
	def __init__(self, n, trading_fee=0):
		#self.portfolio = np.ones(n)/n
		self.portfolio = np.zeros(n)
		
		self.portfolio[0] = 1
		self.portfolios = [self.portfolio]
		self.trading_fee = trading_fee
		self.margin = 1
		self.value = 1
		self.values = [1]
		self.prices = [np.ones(n)]
		self.price_changes = []
		self.update_times = []
		self.minus_flag = False
    
  #he portfolio, interest is the interest to be paid for holding borrowed assets in futures markets for example
	def update(self, time, price_changes, interest=0):
		#keep track of the portfolio update time, might be worth checking that there are no 
		self.update_times.append(time)
		self.price_changes.append(price_changes)
		self.prices.append(self.prices[-1] * price_changes)
		
		profit = (np.sum(np.array(price_changes) * self.portfolio) - np.sum(self.portfolio)) * self.value
		self.value += profit


		if np.sum(np.abs(self.portfolio)) > 0:
			interest_cost = self.portfolio * interest
			self.value -= np.sum(interest_cost) * self.value

			self.portfolio *= price_changes
			self.portfolio /= 1 if np.sum(np.abs(self.portfolio)) == 0 else (np.sum(np.abs(self.portfolio)) / self.margin)

		#pick next portfolio
		target_portfolio = self.calculate_next_portfolio()
		
		trade = target_portfolio - self.portfolio
		#print('target portfolio', target_portfolio)	

		self.execute_trade(trade)


		if self.minus_flag==False:
			self.values.append(self.value * self.fees(time))		
		else:
			self.values.append((self.value * self.fees(time)+self.values[-1])/2)		      
			self.value=(self.value * self.fees(time)+self.values[-1])/2

		#update data
		if self.value * self.fees(time)/self.values[-2]<1.0:
			self.minus_flag=True
		else:
			self.minus_flag=False
		
		self.portfolios.append(np.array(self.portfolio))
