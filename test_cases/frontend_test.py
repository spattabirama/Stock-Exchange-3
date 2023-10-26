import unittest
import requests

frontend_server_address = 'localhost'
frontend_server_port = 6173


class TestMyHandler(unittest.TestCase):
    # TC1 - Create a mock GET request to retrieve stock data for a known stock
    def test_known_stock_lookup(self):
        response = requests.get(f"http://{frontend_server_address}:{frontend_server_port}/stocks/GameStart")
        lookup_response = response.json()
        print(f"Request sent: http://{frontend_server_address}:{frontend_server_port}/stocks/GameStart")
        print("Response received: ", lookup_response)
        # Check if the stock data is returned in the expected format
        self.assertIsInstance(lookup_response, dict, "Response is not in the expected format")
        self.assertIn("data", lookup_response.keys())
        data = lookup_response['data']
        self.assertIn("name", data.keys())
        self.assertIn("price", data.keys())
        self.assertIn("quantity", data.keys())
        print("\n")

    # TC2 - Create a mock GET request to retrieve stock data for an unknown stock
    def test_unknown_stock_lookup(self):
        response = requests.get(f"http://{frontend_server_address}:{frontend_server_port}/stocks/BeerCo")
        lookup_response = response.json()
        print(f"Request sent: http://{frontend_server_address}:{frontend_server_port}/stocks/BeerCo")
        print("Response received: ", lookup_response)
        # Check if the stock data is returned in the expected format
        self.assertEqual(lookup_response, {"error": {"code": 404, "message": "stock not found"}})

    # TC3 - Create a mock post request to buy valid stock
    def test_buy_known_stock(self):
        order = {"name": "GameStart", "quantity": 2, "type": 'buy'}
        response = requests.post(f"http://{frontend_server_address}:{frontend_server_port}/orders", json=order)
        post_response = response.json()
        print("Order: ", order)
        print(f"Request sent: http://{frontend_server_address}:{frontend_server_port}/orders")
        print("Response received: ", post_response)
        # Check if the trade details are returned in the expected format
        self.assertIsInstance(post_response, dict, "Response is not in the expected format")
        self.assertIn("data", post_response.keys())
        data = post_response['data']
        self.assertIn("transaction_number", data.keys())
        self.assertIn("name", data.keys())
        self.assertIn("quantity", data.keys())
        self.assertIn("type", data.keys())
        print("\n")

    # TC4 - Create a mock post request to buy stock that exceeds the trading volume
    def test_buy_known_stock_exceed_qty(self):
        order = {"name": "GameStart", "quantity": 2000, "type": 'buy'}
        response = requests.post(f"http://{frontend_server_address}:{frontend_server_port}/orders", json=order)
        post_response = response.json()
        print("Order: ", order)
        print(f"Request sent: http://{frontend_server_address}:{frontend_server_port}/orders")
        print("Response received: ", post_response)
        # Check if the response returns proper error
        self.assertIsInstance(post_response, dict, "Response is not in the expected format")
        self.assertEqual(post_response, {"error": {"code": 403, "message": 'Not enough stock'}})
        print("\n")

    # TC5 - Create a mock post request to buy invalid stock
    def test_buy_unknown_stock(self):
        order = {"name": "BeerCo", "quantity": 5, "type": 'buy'}
        response = requests.post(f"http://{frontend_server_address}:{frontend_server_port}/orders", json=order)
        post_response = response.json()
        print("Order: ", order)
        print(f"Request sent: http://{frontend_server_address}:{frontend_server_port}/orders")
        print("Response received: ", post_response)
        # Check if the response returns proper error
        self.assertIsInstance(post_response, dict, "Response is not in the expected format")
        self.assertEqual(post_response, {"error": {"code": 404, "message": "stock not found"}})
        print("\n")

    # TC6 - Create a mock post request to sell valid stock
    def test_sell_known_stock(self):
        order = {"name": "GameStart", "quantity": 2, "type": 'sell'}
        response = requests.post(f"http://{frontend_server_address}:{frontend_server_port}/orders", json=order)
        post_response = response.json()
        print("Order: ", order)
        print(f"Request sent: http://{frontend_server_address}:{frontend_server_port}/orders")
        print("Response received: ", post_response)
        # Check if the stock data is returned in the expected format
        self.assertIsInstance(post_response, dict, "Response is not in the expected format")
        self.assertIn("data", post_response.keys())
        data = post_response['data']
        self.assertIn("transaction_number", data.keys())
        self.assertIn("name", data.keys())
        self.assertIn("quantity", data.keys())
        self.assertIn("type", data.keys())
        print("\n")

    # TC7 - Create a mock post request to sell invalid stock
    def test_sell_unknown_stock(self):
        order = {"name": "BeerCo", "quantity": 5, "type": 'sell'}
        response = requests.post(f"http://{frontend_server_address}:{frontend_server_port}/orders", json=order)
        post_response = response.json()
        print("Order: ", order)
        print(f"Request sent: http://{frontend_server_address}:{frontend_server_port}/orders")
        print("Response received: ", post_response)
        # Check if the response returns proper error
        self.assertIsInstance(post_response, dict, "Response is not in the expected format")
        self.assertEqual(post_response, {"error": {"code": 404, "message": "stock not found"}})
        print("\n")

    # TC8 - Create a mock post invalidation request
    def test_invalidation_request(self):
        stockname = "GameStart"
        print("Stockname: ", stockname)
        print(f"Request sent: http://{frontend_server_address}:{frontend_server_port}/invalidate/{stockname}")
        response = requests.delete(f"http://{frontend_server_address}:{frontend_server_port}/invalidate/{stockname}")
        post_response = response.json()
        print("Response received: ", post_response)
        # Check if the response returns proper error
        self.assertIsInstance(post_response, dict, "Response is not in the expected format")
        self.assertTrue(post_response == {'data': {'message': 'Successfully invalidated'}}
                        or post_response == {'data':{'message':'Stock not present'}}
                        or post_response == {'data': {'message': 'Caching not enabled'}})
        print("\n")

    # TC9 - Create a mock post to check available order
    def test_check_available_order(self):
        order_num = 1
        response = requests.get(f"http://{frontend_server_address}:{frontend_server_port}/orders/{order_num}")
        post_response = response.json()
        print(f"Request sent: http://{frontend_server_address}:{frontend_server_port}/orders/{order_num}")
        print("Response received: ", post_response)
        # Check if the response returns proper error
        self.assertIsInstance(post_response, dict, "Response is not in the expected format")
        self.assertIn("data", post_response.keys())
        data = post_response['data']
        self.assertIn("transaction_number", data.keys())
        self.assertIn("name", data.keys())
        self.assertIn("quantity", data.keys())
        self.assertIn("type", data.keys())
        print("\n")

    # TC10 - Create a mock post to check unavailable order
    def test_check_unavailable_order(self):
        order_num = 0
        response = requests.get(f"http://{frontend_server_address}:{frontend_server_port}/orders/{order_num}")
        post_response = response.json()
        print(f"Request sent: http://{frontend_server_address}:{frontend_server_port}/orders/{order_num}")
        print("Response received: ", post_response)
        # Check if the response returns proper error
        self.assertIsInstance(post_response, dict, "Response is not in the expected format")
        self.assertEqual(post_response, {"error": {"code": 409, "message": 'Order number does not exist'}})
        print("\n")


if __name__ == '__main__':
    unittest.main()
