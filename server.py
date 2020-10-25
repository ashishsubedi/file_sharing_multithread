import socket
from threading import Thread, Lock
from socketserver import ThreadingMixIn
import sys,os

import connection

TCP_IP = 'localhost'
TCP_PORT = 7200
BUFFER_SIZE = 1024

NO_OF_THREADS = 4


FLAG_SEND = 1
FLAG_RECV = 0

END_PATTERN = bytes('ENDCOMM','utf-8')
HEADER_SIZE = 10


flag = -1
recvFlag = -1
filename = ''
def init():
    try:
        #all except tcpsock are of client
        tcpsock,sock ,(ip,port) = connection.startServer()
        
        retry = 1
        while(retry == 1 or retry == '1'):
            status,flag = connection.establishSendRecvConn(sock)
            if not status: return False

            if(flag == FLAG_RECV):
                filename = input("Enter full path of file to receive: ")
            elif flag == FLAG_SEND:
                filename = input("Enter full path of file to send: ")
            else:
                print("Exiting program")
                return False

            if flag == FLAG_RECV:
                try:
                    connection.recvFile(sock,filename)
                except Exception as e:
                    print("Some error occured",e)
                    retry = input("Press 1 to send file again, press any other key to exit")
            

            elif flag == FLAG_SEND:
                try:
                    connection.sendFile(sock,filename)
                except Exception as e:
                    print("Some error occured",e)
                    retry = input("Press 1 to send file again, press any other key to exit")
    except:
        pass
    finally:
        tcpsock.close()

if __name__ == "__main__":
    init()
