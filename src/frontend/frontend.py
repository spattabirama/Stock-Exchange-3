import socket
import requests
import threading
import json
from flask import Flask, request, jsonify
import argparse

#Lock to access catalog_cache
cachelock = threading.Lock()
# Lock to find the leader
leaderlock = threading.Lock()
# Lock to access order server details
configlock = threading.Lock()

# Custom handler for client requests
class FrontendService:
    def __init__(self, host, port,en):
        self.host = host
        self.port = port
        self.catalog_cache = dict()
        self.servers = {}
        self.order_id = 0
        self.orderserver_addr = 0
        self.orderserver_port = 0
        self.cache_en = int(en)
        self.app = Flask(__name__)
        self.setup()
    def find_leader(self):
        # Go through each replica in decreasing order of ID's and find the largest id server
        with configlock:
            for id in self.servers:
                try:
                    response = requests.get(f"http://{self.servers[id][0]}:{self.servers[id][1]}/ping_{id}", timeout=1)
                    if response.status_code == 200:
                            self.order_id = id
                            self.orderserver_addr = self.servers[id][0]
                            self.orderserver_port = self.servers[id][1]
                            break
                except Exception as e:
                    pass

    # Send the leader information to all the order server replicas
    def send_leader_info(self):
        # Create reply which consists of the leader's id,addr and port
            reply = {'data': {'leader': self.order_id, 'addr': self.orderserver_addr, 'port': self.orderserver_port}}
            # Go through each server and sends leader information
            with configlock:
                for id in self.servers:
                    replica_id = id
                    replica_ip = self.servers[id][0]
                    replica_port = self.servers[id][1]
                    # Send the post request to each of the replica servers
                    try:
                        requests.post(f"http://{replica_ip}:{replica_port}/leader_info_{replica_id}", json=reply, timeout=1)
                    # If the server is not up continue sending to the other servers
                    except Exception as e:
                        pass
    # Function to load replica information,find the leader and send leader information at start up
    def setup(self):
        with open('config.json', 'r') as f:
            config = json.load(f)
        for section in config['orderserver']:
            host = section['host']
            port = section['port']
            id = int(section['id'])
            with configlock:
                self.servers[id] = (host, port)
        # Sort the server ids in decreasing order
        with configlock:
            self.servers = dict(sorted(self.servers.items(), reverse=True))
        # Find the leader at start up and send the leader info to all the order replicas
        with leaderlock:
            self.find_leader()
            self.send_leader_info()

        # Function which sends trade requests to the leader of order sever
        @self.app.route('/orders', methods=['POST'])
        def tradestock():
                # Extract the request
                orderdict = request.get_json()
                # Apply lock to send request
                with leaderlock:
                    try:
                        response = requests.post(f"http://{self.orderserver_addr}:{self.orderserver_port}/trade_{self.order_id}",json=orderdict, timeout=3)
                        if response.status_code == 200:
                            return jsonify(response.json())
                        # If the server is up but has not synchronized its database
                        else:
                            # Find the leader and send leader information to all replicas
                            self.find_leader()
                            self.send_leader_info()
                            # Send the request again to the new leader
                            response = requests.post(
                                f"http://{self.orderserver_addr}:{self.orderserver_port}/trade_{self.order_id}",
                                json=orderdict, timeout=2)
                            if response.status_code == 200:
                                return jsonify(response.json())
                            return jsonify({'error': {'message': 'No server is up'}})

                    except Exception as e:
                        # Find the new leader and send the info to all the replicas
                        self.find_leader()
                        self.send_leader_info()
                        try:
                            # Try sending the request again
                            response = requests.post(f"http://{self.orderserver_addr}:{self.orderserver_port}/trade_{self.order_id}",json=orderdict, timeout=2)
                            return jsonify(response.json())
                        except Exception as e:
                            return jsonify({'error': {'message': 'No server is up'}})

        # The function is used to invalidate an already existing stock which was traded
        @self.app.route('/invalidate/<stockname>', methods=['DELETE'])
        def invalidate_cache(stockname):
            # Check if caching feature is enabled
            if self.cache_en:
                with cachelock:
                    # Remove the stock if it is present
                    if stockname in self.catalog_cache:
                        self.catalog_cache.pop(stockname)
                        return jsonify({'data': {'message': 'Successfully invalidated'}})
                    else:
                        return jsonify({'data':{'message':'Stock not present'}})
            return jsonify({'data': {'message': 'Caching not enabled'}})


        # Send http request to check if the transaction exists in the order server
        @self.app.route('/orders/<ordernum>', methods=['GET'])
        def checkstock(ordernum):
                #Take the leader lock and send request
                with leaderlock:
                    try:
                        response = requests.get(f"http://{self.orderserver_addr}:{self.orderserver_port}/checkorder_{self.order_id}/{ordernum}")
                        if response.status_code == 200:
                                    return jsonify(response.json())
                        # Run election and resend if the order server is not active
                        else:
                            self.find_leader()
                            self.send_leader_info()
                            response = requests.get(
                                f"http://{self.orderserver_addr}:{self.orderserver_port}/checkorder_{self.order_id}/{ordernum}")
                            if response.status_code == 200:
                                return jsonify(response.json())
                            return jsonify({'error': {'code':403,'message': 'No server is up'}})
                    # Run election and resend if order server is not up
                    except Exception as e:
                        self.find_leader()
                        self.send_leader_info()
                        try:
                            response = requests.get(f"http://{self.orderserver_addr}:{self.orderserver_port}/checkorder_{self.order_id}/{ordernum}")
                            if response.status_code == 200:
                                return jsonify(response.json())
                        except Exception as e:
                            return jsonify({'error': {'code':403,'message': 'No order server is up'}})



        # Function which communicates with catalogServer using HTTP Rest API
        @self.app.route('/stocks/<stockname>', methods=['GET'])
        def lookupstock(stockname):

                # Check if cache enable feature is activated
                if self.cache_en:
                    # Apply cache lock to access in-memory cache
                    with cachelock:
                        # Check in-memory cache for stock name and return stock details if found
                        if stockname in self.catalog_cache:
                            return self.catalog_cache[stockname]
                catalog_server_address = 'localhost'
                catalog_server_port = 8103
                # Sends a lookup request using the exposed function by the catalogServer which takes as input the stock name
                response = requests.get(f"http://{catalog_server_address}:{catalog_server_port}/lookup/{stockname}")
                lookupresponse = response.json()

                if self.cache_en:
                    # Caches the result after every lookup
                    with cachelock:
                        self.catalog_cache[stockname] = lookupresponse
                return jsonify(lookupresponse)



    # This starts the multithreaded flask application
    def start(self):
        self.app.run(host=self.host, port=self.port)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # pick whether to enable cache or not
    parser.add_argument("--cache_en", type=str, default="1")
    args = parser.parse_args()
    cache_en = args.cache_en
    obj = FrontendService(socket.gethostname(), 6173, cache_en)
    obj.start()



