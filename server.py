import socket
import sys
import selectors
import types

commonbuff = []
users = {}

#------------------FUNCTION-DEFINITIONS-------------------------
def accept_wrapper(sock):
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)
    username = conn.recv(1024)
    users[str(addr)] = username.decode()
    commonbuff.append(users[str(addr)] + " has joined the server")
        
sel = selectors.DefaultSelector()


def service_connection(key, mask, burst):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            commonbuff.append(users[str(data.addr)] + ":" + " " + recv_data.decode())
        else:
            print(f"Closing connection to {data.addr}")
            commonbuff.append(users[str(data.addr)] + " has left the server")
            sel.unregister(sock)
            sock.close()
            del users[str(data.addr)]
    if mask & selectors.EVENT_WRITE:
        if commonbuff:
            for i in range(burst):
                print(f"Sending {commonbuff[i].encode()} to {data.addr}")
                sent = sock.sendall(commonbuff[i].encode())  # Should be ready to write
                


#...

host, port = sys.argv[1], int(sys.argv[2])
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((host, port))
lsock.listen()
print(f"Listening on {(host, port)}")
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

try:
    while True:
        burst = len(commonbuff)
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                service_connection(key, mask, burst)
        commonbuff = commonbuff[burst:]
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    sel.close()



