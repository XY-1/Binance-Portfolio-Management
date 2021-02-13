"""
Script to Download Hourly data from the binance REST API

Author: Alfred Holmes, https://github.com/alfredholmes

"""

import requests, json, sqlite3, datetime, decimal

#MARKETS = ['BTCUSDT', 'ETHBTC', 'BNBBTC', 'EOSBTC']
#MARKETS = ['BTCUSDT', 'ETHUSDT', 'EOSUSDT', 'LTCUSDT', 'BNBUSDT', 'XRPUSDT', 'BCHUSDT', 'ADAUSDT', 'XMRUSDT']
MARKETS  = ['BTCUSDT', 'ETHUSDT', 'EOSUSDT', 'LTCUSDT', 'BNBUSDT', 'XRPUSDT', 'BCHUSDT', 'ADAUSDT', 'XMRUSDT', 'LSKUSDT', 'FCTUSDT', 'XEMUSDT', 'MONAUSDT', 'XLMUSDT', 'QTUMUSDT', 'BATUSDT', 'IOSTUSDT', 'ENJUSDT', 'DOGEUSDT', 'DOTUSDT', 'LINKUSDT', 'ATOMUSDT', 'TRXUSDT', 'IOTAUSDT' ,'VETUSDT', 'XTZUSDT', 'THETAUSDT', 'NEOUSDT', 'FTTUSDT', 'MKRUSDT', 'DASHUSDT', 'ETCUSDT', 'ZRXUSDT', 'DCRUSDT', 'ZILUSDT', 'WAVESUSDT' ,'SCUSDT', 'AEUSDT', 'MANAUSDT','NANOUSDT','ONTUSDT','ZECUSDT','DGBUSDT','OMGUSDT','HBARUSDT','ICXUSDT','ZENUSDT','KNCUSDT','BNTUSDT','RVNUSDT','OCEANUSDT','MATICUSDT']

START_DATE = datetime.datetime(year=2020, month=1, day=1)
N = 1000
INTERVAL = '30m'
INTERVALS = {
			 '1m': 60 * 1000,

			 '3m': 3 * 60 * 1000,
			 '5m': 5 * 60 * 1000,
			 '15m': 15 * 60 * 1000,
			 '30m': 30 * 60 * 1000,
			 '1h':  60 * 60 * 1000,

			 '2h': 2 * 60 * 60 * 1000,
			 '4h': 4 * 60 * 60 * 1000,
			 '6h': 6 * 60 * 60 * 1000,
			 '8h': 8 * 60 * 60 * 1000,

			 '12h': 12 * 60 * 60 * 1000,
			 '1d':  24 * 60 * 60 * 1000,

			 '3d': 3 * 24 * 60 * 60 * 1000,
			 '1w': 7 * 24 * 60 * 60 * 1000

			}

LIMIT = 1000 #number of candles to return

DATABASE = 'data/futures_candles_' + INTERVAL + '.db'


def get_position(value, a):
	a = a[:] + [value]
	a.sort()
	return a.index(value)




def main():
	db = sqlite3.connect(DATABASE)
	c = db.cursor()
	columns = ''
	for market in MARKETS:
		columns += market + '_open float, ' + market + '_close float,' + market + '_high float,' + market + '_low float,' + market + '_volume float,' + market + '_funding_rate float,'

	try:
		c.execute('DROP TABLE CANDLES')
		pass
	except:
		pass


	c.execute('CREATE TABLE CANDLES (id integer PRIMARY KEY, open_time integer, ' + columns[:-1] + ');')


	start_ms = int(START_DATE.timestamp() * LIMIT)
	end_ms = start_ms + N * INTERVALS[INTERVAL] * LIMIT

	times = [start_ms + i * INTERVALS[INTERVAL] for i in range(N * LIMIT)]


	#dicts to hold data
	now = datetime.datetime.now().timestamp() * 1000
	interval_data = {time: {market: [] for market in MARKETS} for time in times if time < now}
	initial_values = {}

	for market in MARKETS:
		fundingRates = []
		current_ms = start_ms
		while current_ms < end_ms:
			params = {
				'symbol': 'BTCUSDT',
				'startTime': current_ms,
				'limit': LIMIT,
				'extra_param': 'lol'
			}
			r = requests.get('https://fapi.binance.com/fapi/v1/fundingRate', params=params)
			result = json.loads(r.text)
			if len(result) == 0 and len(fundingRates) > 0:
				break


			current_ms = result[-1]['fundingTime'] + 1
			fundingRates += result

		for i in range(N):
			current_ms = start_ms + i * 1000 * INTERVALS[INTERVAL]


			print(current_ms)
			if current_ms > now:
				print('Querying future candles')
				break


			params = {
				'symbol': market,
				'interval': INTERVAL,
				'startTime': current_ms,
				'endTime': current_ms + LIMIT * INTERVALS[INTERVAL],
				'limit': LIMIT
			}
			r = requests.get('https://fapi.binance.com/fapi/v1/klines', params=params)

			candles = json.loads(r.text)
			for candle in candles:
				if candle[0] > now:
					break
				id = get_position(candle[0], [f['fundingTime'] for f in fundingRates])
				if id + 1 >= len(fundingRates):
					rate = float(fundingRates[-1]['fundingRate'])
				else:
					rate = float(fundingRates[id + 1]['fundingRate'])


				try:
					interval_data[candle[0]][market] = candle[1:] + [rate]
				except KeyError:
					print('Key Error:', market, (candle[0] - start_ms) / INTERVALS[INTERVAL])
					actual = int((candle[0] - start_ms) / INTERVALS[INTERVAL]) * INTERVALS[INTERVAL] + start_ms
					interval_data[actual][market] = candle[1:] + [rate]

			if market not in initial_values:
				if len(candles) > 0:
					initial_values[market] = candles[0][1:] + [0]
				else:
					print('length of ' + market + '0')



	#make sure the initial value for each market is not empty
	interval_data[start_ms] = initial_values

	#add to the database
	previous_values = initial_values


	print(interval_data)
	for time in times:
		if time > now:
			continue

		data = {'open_time': time}


		for market in MARKETS:
			candle = interval_data[time][market]
			if candle == []:
				candle = previous_values[market]
			else:
				previous_values[market] = candle

			#array indicies documented in binance API docs
			open_price = candle[0]
			high_price = candle[1]
			low_price = candle[2]
			close_price = candle[3]
			volume = candle[4]
			funding_rate = candle[-1]





			data[market + '_open'] = open_price
			data[market + '_high'] = high_price
			data[market + '_low'] = low_price
			data[market + '_close'] = close_price
			data[market + '_volume'] = volume
			data[market + '_funding_rate'] = funding_rate

		#now add to the database

		keys = ''
		values = ''

		for key, value in data.items():
			keys += key + ', '
			values += str(value) + ', '

		keys = keys[:-2]
		values = values[:-2]
		c.execute('INSERT INTO CANDLES (' + keys + ') VALUES (' + values +')')


	db.commit()




	start_ms + INTERVALS[INTERVAL]

if __name__ == '__main__':
	main()
