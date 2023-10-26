import socket
import threading
import time
import csv
import requests
from flask import Flask,request,jsonify
'''
- Implemented a catalogservice class which initially loads data from the file,defines lookup and trade functions
and also periodically backs up data to the file
'''
frontend_server_address = socket.gethostname()
frontend_server_port = 6173
stock_path = 'backend/files/stockCatalog.csv'
class stockValues:
    def __init__(self, quantity,volume,price):
        self.quantity = quantity
        self.volume = volume
        self.price = price

# Added locks for stock catalog and for writing to csv
cataloglock = threading.Lock()
orderlock = threading.Lock()
class CatalogServer:
    def __init__(self,host,port):
        self.host = host
        self.port = port
        self.catalog = dict()
        self.app = Flask(__name__)
        # loads data initially
        self.load()
        th = threading.Thread(target=self.backup_data)
        th.start()
        self.setup()

    # Backs data to the file periodically
    def backup_data(self):
        while True:
            time.sleep(3)
            # Lock to access the catalog and update the csv file
            with cataloglock:
                lst = []
                lst.append(['Stockname', 'Quantity', 'Volume_traded', 'Price'])
                for name in self.catalog:
                    lst.append([name, self.catalog[name].quantity, self.catalog[name].volume, self.catalog[name].price])
                with orderlock:
                    with open(stock_path, 'w') as csvfile:
                        csvwriter = csv.writer(csvfile)
                        csvwriter.writerows(lst)

    def load(self):
            f = open(stock_path, 'r')
            next(f)
            for line in f:
                name, values = line.split(",")[0], line.split(",")[1:]
                self.catalog[name] = stockValues(int(values[0]),int(values[1]),float(values[2].strip()))
            print('Succesfully loaded data')

    def setup(self):

        @self.app.route('/lookup/<stockname>',methods=['GET'])
        def lookup(stockname):
            # Apply catalog lock to access the catalog
            with cataloglock:
                # stock does not exist
                if stockname not in self.catalog:
                    res = {"error": {"code": 404, "message": "stock not found"}}
                    return jsonify(res)
                # retrieve stock from the catalog
                quantity, price = self.catalog[stockname].quantity, self.catalog[stockname].price
                res = {"data": {"name": stockname, "price": price, "quantity": quantity}}
                return jsonify(res)

        @self.app.route('/update', methods=['POST'])
        def trade():
            values_dict = request.get_json()
            stockname = values_dict['name']
            qty = values_dict['quantity']
            traded_vol = values_dict['traded']
            # Update stock quantity and volume
            with cataloglock:
                self.catalog[stockname].quantity += qty
                self.catalog[stockname].volume += traded_vol
                res = {"data": {"message": "Success"}}
                # Send invalidation request to the frontendService
                requests.delete(f"http://{frontend_server_address}:{frontend_server_port}/invalidate/{stockname}")
                return jsonify(res)
    def start(self):
        self.app.run(host=self.host,port=self.port)
obj = CatalogServer('localhost',8103)
obj.start()



