import curses
from curses import wrapper
from curses.textpad import Textbox, rectangle
import sys
import socket
import time
import selectors
import types

username = input("Enter username: ")
sel = selectors.DefaultSelector()
messages = []
inbuff = []
running = True

def start_connections(host, port):
    server_addr = (host, port)
    inbuff.append("Starting connection to {server_addr}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.connect_ex(server_addr)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    data = types.SimpleNamespace(
        msg_total=sum(len(m) for m in messages),
        recv_total=0,
        messages=messages,
        outb=b"",
    )
    sel.register(sock, events, data=data)
    sock.sendall(username.encode())
    sock.setblocking(False)
    


def service_connection(key, mask, win, box):
    global running
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            #print(f"{recv_data.decode()}")
            inbuff.append(recv_data.decode())
            data.recv_total += len(recv_data)

    if mask & selectors.EVENT_WRITE:
        if not data.outb and data.messages:
            data.outb = data.messages.pop(0)
        if data.outb:
            #print(f"Sending {data.outb.decode()} to server...")
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]
    if not messages:
        try:
            key = win.getkey()
            box.edit()
            msg = box.gather().replace("\n", "").strip()
            if msg == "QUIT":
                inbuff.append("Closing connection...")
                running = False
            elif msg == "":
                pass
            else:
                messages.append(msg.encode())
                data.msg_total += len(msg.encode())
        except curses.error:
            pass



def main(stdscr):
    start_connections(sys.argv[1], int(sys.argv[2]))

    i = 4
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    gb = curses.color_pair(1)
    stdscr.attron(gb)
    win = curses.newwin(2, 60, 1, 1)
    win.nodelay(True)
    box = Textbox(win)
    rectangle(stdscr, 0, 0, 3, 61)
    print("Reached")
    try:

        while (running):
            events = sel.select(timeout=None)

            for key, mask in events:
                service_connection(key, mask, win, box)

            if (i >= 25):
                stdscr.clear()
                i = 4
            stdscr.refresh()

            if inbuff:
                stdscr.addstr(i, 0, inbuff.pop(0))
                i += 1

    except KeyboardInterrupt:
        print("Keyboard Interrupt detected")
    finally:

        try:
            key, mask = events[0]
            lastmsg = key.fileobj.recv(1024)
            stdscr.addstr(0+i, 0, lastmsg.decode())
            sel.unregister(key.fileobj)
            key.fileobj.close()
        except BlockingIOError:
            sel.unregister(key.fileobj)
            key.fileobj.close()

wrapper(main)
