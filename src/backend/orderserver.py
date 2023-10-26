import socket
import threading
import json
import requests
import csv
from flask import Flask,request,jsonify
import argparse
import os
import time

#Lock when accessing count varibale
transactionlock = threading.Lock()
# Lock when accessing database file
writelock = threading.Lock()
# Apply lock when updating leader
leaderlock = threading.Lock()
# Lock for checking if the server is synchronized
activelock = threading.Lock()
#Lock for accessing orderserver configurations
configlock = threading.Lock()
# Catalog server address and port
catalog_server_address = 'localhost'
catalog_server_port = 8103

# server class which has methods for various requests
class orderserver:

    # self.count is the transaction number which is incremented whenever a transaction is successful
    #The count is assigned to 0 before the server start
    def __init__(self,host,port):
        self.count = 0
        self.host = host
        self.port = port
        self.active = False
        self.orderservers=dict()
        self.leader = 0
        self.leader_addr = 0
        self.leader_port = 0
        self.app = Flask(__name__)
        self.setup()
    def setup(self):
        # On startup,the order server checks for the state from the replicas and updates its file
        # Gets and stores all the replica information in the form of id:(host,port) in a dictionary
        def get_replica_configs():
            with open('config.json', 'r') as f:
                config = json.load(f)
            for section in config['orderserver']:
                replica_id = section['id']
                replica_ip = section['host']
                replica_port = section['port']
                with configlock:
                    self.orderservers[replica_id] = (replica_ip,replica_port)
        # Finds the leader at startup by sending messages to all replica id's
        def update_leader():
            # Go through all replica id's
            with configlock:
                for replica_id in self.orderservers:
                    if replica_id != id:
                        replica_ip = self.orderservers[replica_id][0]
                        replica_port = self.orderservers[replica_id][1]
                        try:
                            # Send a request to find the leader id
                            response = requests.get(f"http://{replica_ip}:{replica_port}/find_leader_{replica_id}",timeout=1)
                            if response.status_code == 200:
                                leaderdata = response.json()
                                # update the leader
                                with leaderlock:
                                    self.leader = leaderdata['data']['leader_id']
                                    self.leader_addr = leaderdata['data']['addr']
                                    self.leader_port = leaderdata['data']['port']
                                break
                        # Check other id's for leader information
                        except requests.exceptions.Timeout:
                            pass
                        except requests.ConnectionError:
                            pass

        # Synchronises current database file with the leader at startup
        def synchronize_database():
                # Find the leader order server
                update_leader()
                # Take a writelock and update database
                with writelock:
                    with open(order_path,'r') as f:
                        reader = csv.reader(f)
                        rows = list(reader)
                        # Find the last transaction number
                        trnum = rows[-1][0]
                    # Generate query with the next transaction number to extract rows after a particular row
                    # If the file is empty,synchronise everything
                    if trnum =='transaction_number':
                        trnum = 0
                    # Create a request query
                    sync_query = {'transaction_number':trnum}

                    try:
                        # Send a synchronization request to leader server
                        with leaderlock:
                            response = requests.post(f"http://{self.leader_addr}:{self.leader_port}/databasesync_{self.leader}",json=sync_query,timeout=1)
                        if response.status_code == 200:
                            rows = response.json()
                            with open(order_path, 'a') as f:
                                writer = csv.writer(f)

                                for row in rows:
                                    values = [row['transaction_number'], row['name'], row['quantity'], row['type']]
                                    writer.writerow(values)
                        # else: Nothing to synchronise or the order server is not up.Here we make sure that atleast one replica of the order server is up
                    # Leader is already extracted and the above request is assumed to go through,if this is the first server to be up,no synchronisation takes place
                    except Exception as e:
                        pass
                # Once the database is initially synchronised it is ready to take new trade synchronisations.
                # This is set even when there is no synchronisation as this case arises when either the database is upto date or when it is the first replica to be up
                with activelock:
                    self.active = True

        # Find replica configs at startup
        get_replica_configs()
        # Synchronize the database file
        synchronize_database()

        # Given an ordernumber,check if the file contains it
        def read_file(ordernum):
            rows_with_value = {}
            with writelock:
                with open(order_path, 'r') as file:
                        # Read the contents of the file
                        lines = file.readlines()
                        # Split the first line into a list of column names
                        headers = lines[0].strip().split(',')
                        # Find the index of the column to search for the value
                        column_to_search_index = headers.index('transaction_number')
                        # Loop over the remaining lines in the file
                        for line in lines[1:]:
                            # Split the line into a list of values
                            values = line.strip().split(',')
                            # Check if the value is present in the specified column

                            if int(values[column_to_search_index]) == int(ordernum):
                                # If the value is present, add the entire row to the list
                                for i,val in enumerate(headers):
                                    rows_with_value[val] = values[i]
            return rows_with_value

        # leader sends transaction details to all replicas after a trade request
        def send_messages_replicas(reply):
            # Wait for some time
            time.sleep(0.02)
            # Go through the replica id's to send trade synchronisation
            with configlock:
                for replica_id in self.orderservers:
                    if replica_id != id:
                        replica_ip = self.orderservers[replica_id][0]
                        replica_port = self.orderservers[replica_id][1]
                        try:
                            # Send synchronise message
                            # Not checking the response as the response doesn't matter.If the replica is not up,it doesn't synchronize.
                            requests.post(f"http://{replica_ip}:{replica_port}/synchronise_{replica_id}",json = reply,timeout=1.5)
                        except requests.exceptions.Timeout:
                            pass
                        except requests.ConnectionError:
                            pass

        # Gives the leader value
        @self.app.route(f'/find_leader_{id}', methods=['GET'])
        def find_leader():
            with activelock:
                if self.active:
                    # Send the details of the leader if it is active
                    with leaderlock:
                        return jsonify({'data':{'leader_id':self.leader,'addr':self.leader_addr,'port':self.leader_port}})
                return jsonify({'error':{'code':400,'message':'Serve not up'}}),400


        # Sends synchronization data to the replica which is just up
        @self.app.route(f'/databasesync_{id}', methods=['POST'])
        def databasesync():
            with activelock:
                if self.active:
                    # Extract data from the request
                    data = request.get_json()
                else:
                    # If the server is not active,cannot send messages
                    return jsonify({'data':{'message','server not up'}}),400
            # Find the transaction number to send requests
            trnum = int(data['transaction_number'])+1
            #Take a write lock and read the file to extract rows with transaction number greater than equal to trnum
            with writelock:
                    with open(order_path,'r') as f:
                        rows = list(csv.reader(f))
                    # if the file is empty,nothing to sync
                    if len(rows) == 1:
                        return jsonify({'data':{'message':'Nothing to sync'}})
                    #Find the index of transaction_number field
                    column_index = rows[0].index('transaction_number')
                    new_rows = []
                    # Append all the rows that have transaction number greater than or equal to trnum
                    for row in rows[1:]:
                        if int(row[column_index]) >= trnum:
                            content = {'transaction_number':row[0],'name':row[1],'quantity':row[2],'type':row[3]}
                            new_rows.append(content)
                    return jsonify(new_rows)








        # Updates the leader info
        @self.app.route(f'/leader_info_{id}', methods=['POST'])
        def leader_info():
            response = request.get_json()
            # Take the leader lock and update leader information
            with leaderlock:
                self.leader = response['data']['leader']
                self.leader_addr = response['data']['addr']
                self.leader_port = response['data']['port']
            return jsonify({'data':{'message':'Success'}})


        # Synchronize database with the updated trade request when it is the replica
        @self.app.route(f'/synchronise_{id}', methods=['POST'])
        def synchronise():
            # Only synchronize when the server is active
            with activelock:
                if self.active:
                    data = request.get_json()
                else:
                    return jsonify({'data': {'message': 'Server not up yet'}})
            # Make a row to add data
            row = []
            row.append(data['data']['transaction_number'])
            row.append(data['data']['name'])
            row.append(data['data']['quantity'])
            row.append(data['data']['type'])
            # Synchronise the counter
            with transactionlock:
                    # Update the count to the latest transaction number
                    self.count = int(data['data']['transaction_number'])
            with writelock:
                    with open(order_path, 'a') as csvfile:
                        # Write the trade request to the replica's database file
                        csvwriter = csv.writer(csvfile)
                        csvwriter.writerow(row)
            return jsonify({'data':{'message':'success'}})




        # Health check to see if the replica is up
        @self.app.route(f'/ping_{id}', methods=['GET'])
        def ping():
            with activelock:
                if self.active:
                    return jsonify({'data':{'message':'active'}}),200
                else:
                    return jsonify({'error':{'code':400,'message':'not active'}}),400

        # The function checks if an order with an order number is present
        @self.app.route(f'/checkorder_{id}/<ordernum>', methods=['GET'])
        def checkorder(ordernum):
            # Check if the server is active
            with activelock:
                if self.active:
                    # Read the ordercatalog for the order number
                    res = read_file(ordernum)
                else:
                    return jsonify({'error',{'code':400,'message':'Server not up yet'}}),400
            # If the order number doesnt exist
            if len(res) == 0:
                return jsonify({"error": {"code": 409, "message": 'Order number does not exist'}})
            else:
                return jsonify({'data':res})



        # Sends a lookup request to catalog server,update request to catalog server,updates ordercatalog.csv,sends data to the replicas and returns response to the front end
        @self.app.route(f'/trade_{id}', methods=['POST'])
        def trade():
            # Check if the server is active
            with activelock:
                if self.active:
                    new_order = request.get_json()
                else:
                    return jsonify({'error',{'code':400,'message':'Server not up yet'}}),400

            # Extract the stock name and generate a get request
            stockname = new_order['name']
            response_get = requests.get(f"http://{catalog_server_address}:{catalog_server_port}/lookup/{stockname}")
            lookup_dict = response_get.json()
            # If the stock doesn't exist send the error message
            if 'error' in lookup_dict:
                return jsonify(lookup_dict)
            # Extract the leftover quantity for the given stock
            available_qty = lookup_dict['data']['quantity']
            # Pick the quantity and type of transaction from the input order
            quantity = new_order['quantity']
            ty = new_order['type']
            # The quantity to reduce or increase depending on buy or sell request.For sell request the quantity is the same
            reduced_quantity = quantity
            if ty == 'buy':
                    # Checks if the current volume is greater than the given quantity
                    if available_qty >= quantity:
                        # Updating the reduced quantity to pass to the catalog server for a buy request
                        reduced_quantity = -quantity
                    else:
                        return jsonify({"error": {"code": 403, "message": 'Not enough stock'}})
            # Generate a post request to be sent to the catalog server
            update_order = {'name':stockname,'quantity':reduced_quantity,'traded':quantity}
            res = requests.post(f"http://{catalog_server_address}:{catalog_server_port}/update",json=update_order)
            update_res = res.json()
            # If the update was successful
            if update_res['data']['message'] == 'Success':
                # Apply transaction lock and increment transaction number and write to csv
                with transactionlock:
                    self.count += 1
                    # Write the updated row into the csv
                    row = [self.count, new_order['name'], new_order['quantity'], new_order['type']]
                    with writelock:
                        with open(order_path, 'a') as csvfile:
                            csvwriter = csv.writer(csvfile)
                            csvwriter.writerow(row)
                        # Changed this to send full reply
                        reply = {"data": {"transaction_number": str(self.count),"name":new_order['name'],"quantity":str(new_order['quantity']),"type":str(new_order['type'])}}
                        # Send the transaction details to the replicas
                        send_messages_replicas(reply)
                    return jsonify(reply)
            else:
                return jsonify({"error": {"code": 405, "message": "Unknown error,retry"}})
    # Start the flask application
    def start(self):
        self.app.run(host =self.host,port=self.port)


# Create 3 replicas of order server
if __name__ == '__main__':
    # Define the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--host_ip", type=str, default="localhost")
    parser.add_argument("--port_no", type=str, default="8000")
    parser.add_argument("--id", type=str, default="1")
    # Parse the command line arguments
    args = parser.parse_args()
    host_ip = args.host_ip
    port = args.port_no
    # Pick current server's id
    id = args.id
    # Create initial order path
    order_path = f'backend/files/ordercatalog_{id}.csv'
    # Check if the file already exists,if it doesn't add the header row
    if not os.path.isfile(order_path):
        row = ['transaction_number','name','quantity','type']
        with open (order_path,'w') as file:
            csvwriter = csv.writer(file)
            csvwriter.writerow(row)
    # Create an object for the ip and port of the server and start it
    obj = orderserver(host_ip,port)
    obj.start()
