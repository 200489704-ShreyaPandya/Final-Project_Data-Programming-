from flask import Flask, render_template
import requests
import time
from pymongo import MongoClient
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

clientMarketStockCollection = ""
dataReceiver = ""


def mongoDbConnectionFunction():
    clientConnection = MongoClient(
        "mongodb://abc:abc11@ac-wftutd5-shard-00-00.1sudfex.mongodb.net:27017,ac-wftutd5-shard-00-01.1sudfex.mongodb.net:27017,ac-wftutd5-shard-00-02.1sudfex.mongodb.net:27017/?ssl=true&replicaSet=atlas-fp47j5-shard-0&authSource=admin&retryWrites=true&w=majority")
    global clientMarketStockCollection
    global dataReceiver
    clientMarketStockDatabase = clientConnection.marketPriceDB
    clientMarketStockCollection = clientMarketStockDatabase.marketPriceCollection
    clientMarketStockCollection.delete_many({})
    clientRequestUrl = requests.get("https://cryptingup.com/api/markets")
    if clientRequestUrl.status_code == 200:
        clientResponseData = clientRequestUrl.json()
        clientMarketStockCollection.insert_one(clientResponseData)
        dataReceiver = clientMarketStockCollection.find_one()
        time.sleep(10)
    else:
        exit()


mongoDbConnectionFunction()
scheduler = BackgroundScheduler({'apscheduler.job_defaults.max_instances': 2})
scheduler.add_job(func=mongoDbConnectionFunction, trigger="interval", seconds=86400)
scheduler.start()

# scheduler.shutdown()

clustered_labels = []
for data in dataReceiver['markets']:
    if data not in clustered_labels:
        clustered_labels.append(data['base_asset'])
filtered_clustered_labels = set(clustered_labels)
clustered_labels = list(filtered_clustered_labels)

clustered_exchange = []
for data in dataReceiver['markets']:
    if data not in clustered_exchange:
        clustered_exchange.append(data['exchange_id'])
filtered_clustered_labels = set(clustered_exchange)
clustered_exchange = list(filtered_clustered_labels)

clustered_list = []
for data in clustered_labels:
    price = 0
    counter = 0
    for subData in dataReceiver['markets']:
        if subData['base_asset'] == data:
            price = price + float(subData['price'])
            counter = counter + 1
    clustered_list.append(price/counter)

filtered_clustered_labels = []
for clustered_subList in clustered_list:
    filtered_clustered_labels.append(round(clustered_subList, 2))

values = filtered_clustered_labels

sortedObject = []
counter = 0
for label in clustered_labels:
    end_counter = len(values)
    sortedObject.append({
        "exchange_id": label,
        "price": values[counter]
    })
    counter = counter + 1
    print(counter)

sortedObject.sort(key=lambda x: x['price'])
sortedObject.reverse()

labels = []
values = []
counter = 0
for objects in sortedObject:
    labels.append(objects['exchange_id'])
    values.append(objects['price'])
    counter += 1
    if counter == 10:
        break

colors = [
    "rgb(205, 92, 92)", "#46BFBD", "#FDB45C", "#FEDCBA",
    "#ABCDEF", "#DDDDDD", "#ABCABC", "#4169E1",
    "#C71585", "#FF4500", "#FEDCBA", "#46BFBD"]


@app.route('/table/<exchange_id>')
def collectiveRecords(exchange_id):
    elementById = []
    if exchange_id == "all":
        for x in dataReceiver['markets']:
            elementById.append(x)
    else:
        for x in dataReceiver['markets']:
            if x['exchange_id'].lower() == exchange_id:
                elementById.append(x)
    return render_template('collectiveRecords.html', title='Stock Market Price',
                           users=elementById, len=len(clustered_exchange), ex_id=clustered_exchange,
                           base_id=["BTC", "ETH"])


@app.route('/')
def baseClassAverageRecords():
    valueDescription = labels
    priceDescription = values
    return render_template('averageRecords.html', title="Stock Price", labels=valueDescription, values=priceDescription)


@app.route('/linear/<sub_asset>')
def currentlyTrending(sub_asset):
    topExchangePriceFluctuations = []
    topExchangeDateFluctuations = []
    for x in dataReceiver['markets']:
        if x not in topExchangePriceFluctuations:
            if x['exchange_id'] == "BINANCE" and x['base_asset'] == sub_asset:
                topExchangePriceFluctuations.append(x['price'])
                topExchangeDateFluctuations.append(x['updated_at'])
    filtered_clustered_fluctuations = set(topExchangePriceFluctuations)
    topExchangePriceFluctuations = list(filtered_clustered_fluctuations)
    line_trend_values = topExchangePriceFluctuations
    label_trend_values = topExchangeDateFluctuations
    return render_template('currentTrending.html', values=line_trend_values, linear_lables=label_trend_values, asset=sub_asset)

@app.route('/latestPriceIn/<currencySelector>')
def amountByCurrencyInBinanceExchange():
    labels_value = labels
    line_values = values
    return render_template('averageRecords.html', title="Market place", labels=labels_value, values=line_values)