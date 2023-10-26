import unittest
import requests

catalog_server_address = 'localhost'
catalog_server_port = 8103


class TestMyHandler(unittest.TestCase):
    # TC1 - Create a mock GET request to retrieve stock data for a known stock
    def test_known_stock_lookup(self):
        response = requests.get(f"http://{catalog_server_address}:{catalog_server_port}/lookup/GameStart")
        lookup_response = response.json()
        print(f"Request sent: http://{catalog_server_address}:{catalog_server_port}/lookup/GameStart")
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
        response = requests.get(f"http://{catalog_server_address}:{catalog_server_port}/lookup/BeerCo")
        lookup_response = response.json()
        print(f"Request sent: http://{catalog_server_address}:{catalog_server_port}/lookup/BeerCo")
        print("Response received: ", lookup_response)
        # Check if the stock data is returned in the expected format
        self.assertEqual(lookup_response, {"error": {"code": 404, "message": "stock not found"}})

    # TC3 - Create a mock POST request to update the stock catalog for a given stock
    def test_stock_update(self):
        update_order = {'name': 'GameStart', 'quantity': -2, 'traded': 2}
        print(f"Request sent: http://{catalog_server_address}:{catalog_server_port}/update")
        print("Order to be updated: ", update_order)
        response = requests.post(f"http://{catalog_server_address}:{catalog_server_port}/update", json=update_order)
        update_response = response.json()
        print("Response received: ", update_response)
        # Check if the stock update is a success
        self.assertEqual(update_response, {"data": {"message": "Success"}},
                         "Response is not in the expected format")


if __name__ == '__main__':
    unittest.main()
