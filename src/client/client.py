import random
import time
import requests

#List of 11 stocks with one stock which doesn't exist
stock_names = ['GameStart','FishCo','BoarCo','MehirCo','Hellow','FanCo','WorldCo','FanStart','FrendCo','EnergyCo','LionCo']
# The probability is initially set to 0.5
prob = 0.6
trade_result_cache = []
# Takes the stockName and creates values for trade request
def create_trade_request(stockName):
    trade_req = dict()
    trade_req['name'] = stockName
    trade_req['quantity'] = random.randint(1,10)
    trade_req['type'] = random.choice(['buy','sell'])
    return trade_req

# Connect to the frontendserver and sends get and post requests
def connect():
    frontend_server = 'localhost'
    frontend_server_port = 6173
    for i in range(500):
        # Wait before sending a request
        time.sleep(0.04)
        # Randomly choose a stock
        stockName = random.choice(stock_names)
        # Sends a trade request using the exposed API endpoint
        response = requests.get(f"http://{frontend_server}:{frontend_server_port}/stocks/{stockName}")
        output = response.json()
        ans = random.uniform(0, 1)
        # Check if the stock exists
        if 'error' in output:
            continue

        # If the generated probability is less than the current probability,send a trade request
        elif ans < prob:
                # Create body for trade request
                content = create_trade_request(stockName)
                # Send the trade request
                trade_response =requests.post(f"http://{frontend_server}:{frontend_server_port}/orders",json = content)
                # If the trade is valid,cache the response
                if 'data' in trade_response.json():
                    trade_result_cache.append(trade_response.json())

    # Check if the trade request is consistent
    for value in trade_result_cache:
        ordernum = value['data']['transaction_number']
        response = requests.get(f"http://{frontend_server}:{frontend_server_port}/orders/{ordernum}")
        # Check if the reply is as expected or not
        if 'error' in output or output['data']!=value:
            print(f'Error in response {ordernum}')
            print(f"Actual data,{output['data']}")
            print(f"Expected,{value}")








connect()
