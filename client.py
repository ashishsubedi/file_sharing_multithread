import socket
from time import time
from threading import Thread,Lock
import sys
import os
import connection

FLAG_SEND = 1
FLAG_RECV = 0

END_PATTERN = bytes('ENDCOMM','utf-8')
HEADER_SIZE = 10

NO_OF_THREADS = 4


flag = -1
recvFlag = -1
filename = ''

TCP_IP = 'localhost'
TCP_PORT = 7200
# TCP_IP = '0.tcp.ngrok.io'
# TCP_PORT = 17314
BUFFER_SIZE = 1024

# TCP_IP = input("Enter SERVER address: ")
# TCP_PORT = int(input("Enter server port: "))




if __name__ == "__main__":
    try: 
        
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

        sock.connect((TCP_IP,TCP_PORT))
        retry = 1

        print("Connection Establisehd with Server")
        while (retry == 1 or retry == '1'):
            status,flag = connection.establishSendRecvConn(sock,False)
            print("Flag ",flag)
            if not status: sys.exit(1)

            if(flag == FLAG_RECV):
                filename = input("Enter full path of file to receive: ")
            elif flag == FLAG_SEND:
                filename = input("Enter full path of file to send: ")
            else:
                print("Exiting program")
                sys.exit(1)
            totalBytes = 0
            if flag == FLAG_RECV:
                try:
                    print("Waiting for sender")
                    connection.recvFile(sock,filename)
                    print(f"\nDownload Complete... {str(totalBytes):>{HEADER_SIZE}} bytes downloaded\t\t")

                except Exception as e:
                    print("Some error occured",e)
                    retry = input("Press 1 to send file again, press any other key to exit")
            
            elif flag == FLAG_SEND:
                try:
                    connection.sendFile(sock,filename)
                except Exception as e:
                    print("Some error occured",e)
                    retry = input("Press 1 to send file again, press any other key to exit")
            
            
            retry = input("Press 1 to send file again, press any other key to exit")
    except Exception as e:
        print("Error",e)
    finally:
        sock.close()
            
