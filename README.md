# Local Proxy Server
A web proxy server which fetches items from the Web on behalf of a Web client (i.e browser) instead of the client fetching them directly. Supports caching of pages and access control.

### What the program can do:
1. Respond to HTTP & HTTPS requests and should display each request on a management
console. It should forward the request to the Web server and relay the response to the browser.
2. Handle Websocket connections.
3. Dynamically block selected URLs via the management console.
4. Efficiently cache HTTP requests locally and thus save bandwidth. You must gather timing and
bandwidth data to prove the efficiency of your proxy.
5. Handle multiple requests simultaneously by implementing a threaded server.
