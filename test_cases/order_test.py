import unittest
import requests

order_server_address = 'localhost'
order_server_port = 8104
order_server_id = 3


class TestMyHandler(unittest.TestCase):
    # TC1 - Create a mock post request to buy valid stock
    def test_buy_known_stock(self):
        order = {"name": "GameStart", "quantity": 2, "type": 'buy'}
        response = requests.post(
                        f"http://{order_server_address}:{order_server_port}/trade_{order_server_id}", json=order,
                        timeout=2)
        post_response = response.json()
        print("Order: ", order)
        print(f"Request sent: http://{order_server_address}:{order_server_port}/trade_{order_server_id}")
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

    # TC2 - Create a mock post request to buy stock that exceeds the trading volume
    def test_buy_known_stock_exceed_qty(self):
        order = {"name": "GameStart", "quantity": 2000, "type": 'buy'}
        response = requests.post(
                        f"http://{order_server_address}:{order_server_port}/trade_{order_server_id}", json=order,
                        timeout=2)
        post_response = response.json()
        print("Order: ", order)
        print(f"Request sent: http://{order_server_address}:{order_server_port}/trade_{order_server_id}")
        print("Response received: ", post_response)
        # Check if the response returns proper error
        self.assertIsInstance(post_response, dict, "Response is not in the expected format")
        self.assertEqual(post_response, {"error": {"code": 403, "message": 'Not enough stock'}})
        print("\n")

    # TC3 - Create a mock post request to buy invalid stock
    def test_buy_unknown_stock(self):
        order = {"name": "BeerCo", "quantity": 5, "type": 'buy'}
        response = requests.post(
                        f"http://{order_server_address}:{order_server_port}/trade_{order_server_id}", json=order,
                        timeout=2)
        post_response = response.json()
        print("Order: ", order)
        print(f"Request sent: http://{order_server_address}:{order_server_port}/trade_{order_server_id}")
        print("Response received: ", post_response)
        # Check if the response returns proper error
        self.assertIsInstance(post_response, dict, "Response is not in the expected format")
        self.assertEqual(post_response, {"error": {"code": 404, "message": "stock not found"}})
        print("\n")

    # TC4 - Create a mock post request to sell valid stock
    def test_sell_known_stock(self):
        order = {"name": "GameStart", "quantity": 2, "type": 'sell'}
        response = requests.post(
                        f"http://{order_server_address}:{order_server_port}/trade_{order_server_id}", json=order,
                        timeout=2)
        post_response = response.json()
        print("Order: ", order)
        print(f"Request sent: http://{order_server_address}:{order_server_port}/trade_{order_server_id}")
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

    # TC5 - Create a mock post request to sell invalid stock
    def test_sell_unknown_stock(self):
        order = {"name": "BeerCo", "quantity": 5, "type": 'sell'}
        response = requests.post(
                        f"http://{order_server_address}:{order_server_port}/trade_{order_server_id}", json=order,
                        timeout=2)
        post_response = response.json()
        print("Order: ", order)
        print(f"Request sent: http://{order_server_address}:{order_server_port}/trade_{order_server_id}")
        print("Response received: ", post_response)
        # Check if the response returns proper error
        self.assertIsInstance(post_response, dict, "Response is not in the expected format")
        self.assertEqual(post_response, {"error": {"code": 404, "message": "stock not found"}})
        print("\n")

    # TC6 - Create a mock post to check available order
    def test_check_available_order(self):
        order_id = 3
        order_num = 1
        response = requests.get(f"http://{order_server_address}:{order_server_port}/checkorder_{order_id}/{order_num}")
        post_response = response.json()
        print(f"Request sent: http://{order_server_address}:{order_server_port}/checkorder_{order_id}/{order_num}")
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

    # TC7 - Create a mock post to check unavailable order
    def test_check_unavailable_order(self):
        order_id = 3
        order_num = 0
        response = requests.get(f"http://{order_server_address}:{order_server_port}/checkorder_{order_id}/{order_num}")
        post_response = response.json()
        print(f"Request sent: http://{order_server_address}:{order_server_port}/checkorder_{order_id}/{order_num}")
        print("Response received: ", post_response)
        # Check if the response returns proper error
        self.assertIsInstance(post_response, dict, "Response is not in the expected format")
        self.assertEqual(post_response, {"error": {"code": 409, "message": 'Order number does not exist'}})
        print("\n")

    # TC8 - Create a mock get to ping available order service
    def test_health_check(self):
        order_ids = [1, 2, 3]
        order_server_ports = [8101, 8102, 8104]
        for i in range(len(order_ids)):
            response = requests.get(f"http://{order_server_address}:{order_server_ports[i]}/ping_{order_ids[i]}", timeout=1)
            post_response = response.json()
            print(f"Request sent: http://{order_server_address}:{order_server_ports[i]}/ping_{order_ids[i]}")
            print("Response received: ", post_response)
            # Check if the response returns proper error
            self.assertIsInstance(post_response, dict, "Response is not in the expected format")
            self.assertTrue(response.status_code == 200)
            self.assertEqual(post_response, {'data': {'message': 'active'}})
        print("\n")

    # TC9 - Create a mock get to find leader
    def test_finding_leader(self):
        order_ids = [1, 2, 3]
        order_server_ports = [8101, 8102, 8104]
        for i in range(len(order_ids)):
            response = requests.get(f"http://{order_server_address}:{order_server_ports[i]}/find_leader_{order_ids[i]}",timeout=1)
            post_response = response.json()
            print(f"Request sent: http://{order_server_address}:{order_server_ports[i]}/find_leader_{order_ids[i]}")
            print("Response received: ", post_response)
            # Check if the response returns proper error
            self.assertIsInstance(post_response, dict, "Response is not in the expected format")
            self.assertTrue(response.status_code == 200)
            self.assertIn("data", post_response.keys())
            data = post_response['data']
            self.assertIn("leader_id", data.keys())
            self.assertIn("addr", data.keys())
            self.assertIn("port", data.keys())
        print("\n")

if __name__ == '__main__':
    unittest.main()
