import socket
import threading
import time

blockedList = set()
timings = {}
cache = {}
BUFFER_SIZE = 8192

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

def init_socket():
    try:
        #Initialize socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        # Bind socket for listen
        s.bind(('localhost', 8080)) # set port number
        s.listen(10) # set max number of connections
        while True:
            print("Waiting for connection...\n")
            client_connection, client_address = s.accept()
            print(color.BOLD + "Connection to Client established!" + color.END)
            data = client_connection.recv(BUFFER_SIZE) # Recieve client data
            thread = threading.Thread(target=handle_request, args=(client_connection, client_address, data))
            thread.start()
        
    except Exception:
        print(color.BOLD + color.RED + "Socket init error" + color.END + color.END)

    except KeyboardInterrupt:
        s.close()
        print(color.BOLD + color.RED + "Interrupting Proxy Server!!!" + color.END + color.END)
        while 1:
            webserver = input("Enter website to block (example.com) or exit:")
            if len(webserver) > 0 and webserver != "exit":
                print("Blocked " + webserver)
                blockedList.add(webserver)
            else:
                break
        init_socket() # re-start program when blocked sites have been added


def handle_request(client_connection, client_address, data):
    # Handle Client Browser request
    print("Starting new thread..")
    try:
        data = data.decode("utf-8")
        first_line = data.split('\n')[0]    # parse the first line
        if not first_line: # check not null
            return
        
        url = first_line.split(' ')[1]      # get url
        method = first_line.split(' ')[0]
        print(color.BLUE + color.BOLD + "Connect to URL: " + url + color.END + color.END)
        print ("Method: " + method)
        if method == "CONNECT": # set webserver for HTTPS 
            webserver = url.split(':')[0]
            port = url.split(':')[1]
        else:                   # set webserver for HTTP
            http_pos = url.find("://") # Find ://
            if(http_pos == -1):
                temp = url
            else:
                temp = url[(http_pos+3):] # Rest of URL (:// removed)
            port_pos = temp.find(":") # Find position of the port, if specified, if not will take default number
            # find end of web server name
            webserver_pos = temp.find("/")
            if webserver_pos == -1:
                webserver_pos = len(temp)
            webserver = ""
            port = -1
            if (port_pos==-1 or webserver_pos < port_pos): 
                # Port not specified, set to default port
                port = 80 
                webserver = temp[:webserver_pos] 
            else:
                # Port was specified
                port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
                webserver = temp[:port_pos]

        # Check if website is blocked
        for val in blockedList:
            if val in webserver:
                print("URL is blocked\n")
                client_connection.sendall(b"HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n<html><body>Blocked Host.</body></html>\r\n\r\n") 
                client_connection.close()
                return 
        
        # Cache Section
        start_time = time.time() 
        get_url = cache.get(webserver)
        if get_url is not None:   # check get_url is not empty (not empty == found in cache)
            print(color.BOLD + color.GREEN + "Found URL in Cache" + color.END + color.END)
            client_connection.sendall(get_url)
            end_time =time.time() 
            print(color.GREEN + "-> Request Via Cache: " + str(end_time-start_time)+"'s" + color.END)
            print(color.GREEN + "-> Request Pre-Cached: " + str(timings[webserver])+"'s" + color.END)
            print(color.GREEN + "-> Difference :" + str(timings[webserver]-(end_time-start_time))+"'s\n" + color.END)
        else:
            forward_data(webserver, port, client_connection, client_address, data, method)

    except socket.error as err:
        print(err)
        return 
    finally:
        client_connection.close()

def forward_data(webserver, port, client_connection, client_address, data, method):

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

        if method == "CONNECT":
            try:
                s.connect((webserver, int(port)))
                reply = "HTTP/1.0 200 connection established \r\n"
                reply += "Proxy-agent: Pyx\r\n"
                reply += "\r\n"
                print(color.BOLD + "Connection to Web Server established!" + color.END)
                client_connection.sendall(reply.encode())
            except socket.error as err:
                print(err)
                return 

            client_connection.setblocking(0) # set to non-blocking mode
            s.setblocking(0) # will not wait for buffer to be empty
            # This is necessary for the websocket connection as it allows it to keep running without stalling, instead it will receive a socket.error if the buffer is full and the request cannot be received.

            print ("Websocket set up complete...\n")    
            while True: # loop to keep connection alive 
                try:
                    request = client_connection.recv(BUFFER_SIZE)
                    s.sendall(request)
                except socket.error as err:
                    pass
                try:
                    reply = s.recv(BUFFER_SIZE)      # read response from webserver
                    client_connection.sendall(reply) # forward response to client
                except socket.error as err:
                    pass #do nothing for socket error

        else: # HTTP Connections
            start_time =time.time()
            string_builder = bytearray("",'utf-8')
            s.connect((webserver,int(port)))
            print("Sending request to server...")
            s.send(data.encode())
            s.settimeout(2)
            try:
                while True:
                    reply= s.recv(BUFFER_SIZE)
                    if(len(reply) >0):
                        client_connection.send(reply)
                        string_builder.extend(reply)
                    else:
                        break
            except socket.error:
                pass
            print("Sending response to client...")
            end_time = time.time()
            print("Request took:" + str(end_time-start_time)+"s")
            timings[webserver] = end_time-start_time
            cache[webserver] = string_builder

            s.close()
            client_connection.close()

init_socket()




        #s.settimeout(150)
        #s.connect((webserver, port))
        #s.sendall(data.encode())
#
        #while 1:
        #    # receive data from web server
        #    data = s.recv(BUFFER_SIZE)
#
        #    if (len(data) > 0):
        #        details = str(data.decode()).split("\n")
        #        for string in details:
        #            print('\x1b[0;32;40m' + string + '\x1b[0m') #Print request to management console (with colour)
        #        client_connection.sendall(data)
        #        #client_connection.send(data) # send to browser/client
        #    else:
        #        break




        
        # Parse HTTP headers
        #isHttps = False
        #details = request.split("\n")
        #if details[0].startswith("CONNECT"):  #Determine whether http/https
        #    isHttps = True
        #hostIndex = 0
        #i = 0
        #for string in details:                                          
        #    if(string[ : 4] == "Host"):
        #        hostIndex = i
        #    i = i+1
        #print ("\n")
#
        #destHost = details[hostIndex][6:]     #Extract host name and port from incoming request
        #hostName = destHost.split(":")[0]
#
        #if hostName not in blockedList:
        #    for string in details:
        #        print('\x1b[0;32;40m' + string + '\x1b[0m') #Print request to management console (with colour)
        #    
        #else:
        #    print("This host is blocked\n")                                         #Return blocked host html
        #    client_connection.sendall(b"HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n<html><body>Blocked Host.</body></html>\r\n\r\n")
        #    client_connection.close()







