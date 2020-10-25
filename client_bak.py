import socket
from time import time
from threading import Thread,Lock
import sys
import os

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

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect((TCP_IP,TCP_PORT))

print("Connection Establisehd with Server")

def recvFile(s,msgLen,lock):
    extraBytes = 4
    totalBytes = 0
    while msgLen>0:
        if(msgLen>(BUFFER_SIZE-extraBytes)):
            size = BUFFER_SIZE
        else:
            size = msgLen+extraBytes

        msgLen-=BUFFER_SIZE
        lock.acquire()
        data = s.recv(size)
        # print(data,len(data))
       
        i = int.from_bytes(data[0:4],'big')
        # print(i)
        data = data[4:]
        f = open(filename+str(i),'ab')

        totalBytes += len(data)
        print(f'Downloading... {str(totalBytes):>{HEADER_SIZE}} bytes \n',end='\r',flush=True)
        f.write(data)
        f.close()
        lock.release()


def establishSendRecvConn():
    global flag,recvFlag,filename
    while(flag+recvFlag != 1):
        flag = int(input("Enter 0- Receive \t 1- Send \t Press any other key to exit"))
       

        #Establish flag handshake
        s.send(bytes(str(flag),'utf-8'))
        '''
            Response must be opposite of flag
            For eg, if client is sending file (flag=1), then server must send recieving flag(flag=0) which sums to 1
        '''
        print("Waiting for Server's response")
        recvFlag = int(s.recv(4).decode('utf-8'))

    if(flag+recvFlag == 1):return True
    else: return False


if __name__ == "__main__":
    try: 
        retry = 1

        while (retry == 1 or retry == '1'):
            if not establishSendRecvConn(): sys.exit(1)

            if(flag == FLAG_RECV):
                filename = input("Enter full path of file to receive\n")
            elif flag == FLAG_SEND:
                filename = input("Enter full path of file to send\n")
            else:
                print("Exiting program")
                sys.exit(1)
            totalBytes = 0
            if flag == FLAG_RECV:
                try:
                    print("Waiting for sender")
                    msgLen = int(s.recv(HEADER_SIZE).decode('utf-8'))
                    print(f"Total Download Size: {msgLen} bytes")
                    actSize = msgLen

                    lock = Lock()
                    threadLength = actSize//(NO_OF_THREADS-1)
 
                    extraLength = 0
                    threads = []

                    if(threadLength*(NO_OF_THREADS-1) != actSize):
                        extraLength = 1

                    recvFile(s,msgLen,lock)
                    # for i in range(NO_OF_THREADS-1):
                    #    #Multi threaded reading
                    #     t = Thread(target=recvFile,args=(s,threadLength,lock))
                    #     t.start()
                    #     threads.append(t)
                    # if(extraLength):
                    #     f = open(filename+str(NO_OF_THREADS),'wb')
                    #     recvFile(s,actSize-(threadLength*(NO_OF_THREADS-1)),lock)
                    for t in threads:
                        t.join()
                        
                    print(f"\nDownload Complete... {str(totalBytes):>{HEADER_SIZE}} bytes downloaded\t\t")

                except Exception as e:
                    print("Some error occured",e)
                    retry = input("Press 1 to send file again, press any other key to exit")
            
            elif flag == FLAG_SEND:
                try:
                    with open(filename,'rb') as f:
                        print("Waiting for reveiver")
                        msgLen = os.path.getsize(filename)
                        s.send(bytes(f'{msgLen:<{HEADER_SIZE}}','utf-8'))
                        print(f"Total Upload Size: {msgLen} bytes")
                        actSize = msgLen

                        while True:
                            #Send header
                            l = f.read(BUFFER_SIZE)
                            # while the file contains data after read
                            while(l):
                                totalBytes += len(l)
                                print(f'Uploading... {str(totalBytes):>{HEADER_SIZE}} bytes {str(totalBytes/actSize*100)}% uploaded',end='\r',flush=True)

                                s.sendall(l)
                                l=f.read(BUFFER_SIZE)
                            if not l:
                                print("Upload Complete")
                                break
                except Exception as e:
                    print("Some error occured",e)
                    retry = input("Press 1 to send file again, press any other key to exit")
            
            
            retry = input("Press 1 to send file again, press any other key to exit")
    except:
        pass
    finally:
        s.close()
            
