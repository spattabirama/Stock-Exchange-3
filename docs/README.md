1. Open 6 terminals at src folder of project.
2. Run the following commands to start catalog server, order servers (3), front end server and a client
    <br> a. python3 backend/catalogserver.py
    <br> b. python3 backend/orderserver.py --id 1 --port_no 8101
    <br> c. python3 backend/orderserver.py --id 2 --port_no 8102
    <br> d. python3 backend/orderserver.py --id 3 --port_no 8104
    <br> e. python3 frontend/frontendserver.py --cache_en 1
    <br> f. python3 client/client.py
