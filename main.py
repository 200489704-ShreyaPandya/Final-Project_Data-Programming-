from http import client
from flask import Flask, render_template
import requests
import time
from pymongo import MongoClient
from apscheduler.schedulers.background import BackgroundScheduler
import urllib
import pandas as pd

app = Flask(__name__)

clientCryptoCollection = ""
dataReceiver = ""


def mongoDbConnectionFunction():
    clientConnection = MongoClient("mongodb+srv://keyur12:"+urllib.parse.quote("ks1997@s")+"@cluster0.s6flt6z.mongodb.net/?retryWrites=true&w=majority")
    
    #db = clientConnection.test

    global clientCryptoCollection
    global dataReceiver
    clientCryptoDatabase = clientConnection.cryptoDb
    clientCryptoCollection = clientCryptoDatabase.cryptoCollection
    clientCryptoCollection.delete_many({})
    clientRequestUrl = requests.get("https://api2.binance.com/api/v3/ticker/24hr")
    if clientRequestUrl.status_code == 200:
        clientResponseData = clientRequestUrl.json()
        clientCryptoCollection.insert_many(clientResponseData)
        dataReceiver = clientCryptoCollection.find()
        #print(dataReceiver)
        time.sleep(10)
    else:
        exit()


mongoDbConnectionFunction()
scheduler = BackgroundScheduler({'apscheduler.job_defaults.max_instances': 2})
scheduler.add_job(func=mongoDbConnectionFunction, trigger="interval", seconds=86400)
scheduler.start()

# scheduler.shutdown()

prices = []
timestamps = []
symbol = []
avgPrice = []
volume = []
count = []

for data in dataReceiver:
    #print(data)
    #print(data['askPrice'])
    prices.append(data['askPrice'])
    symbol.append(data['symbol'])
    avgPrice.append(data['weightedAvgPrice'])
    volume.append(data['volume'])
    count.append(data['count'])

dic = {'Symbol':symbol, 'Prices':prices, 'Volume':volume, 'WeightedAvgPrice':avgPrice, 'Count':count}
df = pd.DataFrame(dic)

df['Prices'] = df['Prices'].astype(float)
df['Volume'] = df['Volume'].astype(float)
df['WeightedAvgPrice'] = df['WeightedAvgPrice'].astype(float)
df['Count'] = df['Count'].astype(float)

top_prices_df = df.nlargest(10, ['Prices'])
top_volume_df = df.nlargest(10, ['Volume'])#bar chart
top_traded_df = df.nlargest(10, ['Count']) #pie chart
top_avgprice_df = df.nlargest(5, ['WeightedAvgPrice'])

colors = [
    "rgb(205, 92, 92)", "#46BFBD", "#FDB45C", "#FEDCBA",
    "#ABCDEF", "#DDDDDD", "#ABCABC", "#4169E1",
    "#C71585", "#FF4500", "#FEDCBA", "#46BFBD"]

#---

@app.route('/')
def baseClass():
    symbol = top_traded_df['Symbol'].to_list()
    count = top_traded_df['Count'].to_list()
    return render_template('index.html', title="By Trading Count", labels=symbol, values=count)


@app.route('/volume')
def volume():
    symbol = top_volume_df['Symbol'].to_list()
    vol = top_volume_df['Volume'].to_list()
    return render_template('volume.html', title="By Volume", labels=symbol, values=vol)


@app.route('/price')
def price():
    volume = top_prices_df['Volume'].to_list()
    price = top_prices_df['Prices'].to_list()
    return render_template('price.html', title="By Price", labels=price, values=volume)

if __name__ == '__main__':
    app.run()
