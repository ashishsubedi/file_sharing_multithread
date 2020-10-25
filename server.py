import socket
from threading import Thread, Lock
from socketserver import ThreadingMixIn
import sys,os

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

def sendFile(sock,f,seek,end,lock,part:int):
    '''
    Function to send certain bytes of file
    sock: connected socket to send the file to
    f: file object
    seek: start position from where file to send
    end: how long in bytes of data should be sent
    part: index of the file(starting from 0)
    '''
    while True:
        #Send header
        length = end-seek-1
        readLength = 0
        f.seek(seek,0)
        #BUFFERSIZE-4 because 4 byte for 0 to NO_OF_THREADS
        l = f.read(BUFFER_SIZE-4 if (length-readLength)>(BUFFER_SIZE-4) else (length-readLength))
        readLength+= len(l)

        part_byte = part.to_bytes(4,'big')
        # while the file contains data after read
        # totalBytes = 0
        while(l):
            # totalBytes += len(l)
            print(part,len(part_byte),len(l))
            # print(f'Uploading {part}... {str(totalBytes):>{HEADER_SIZE}} bytes ',end='\r',flush=True)
            lock.acquire()
            sock.send(part_byte)
            sock.sendall(l)
            lock.release()
            if(length<readLength): return
            l = f.read(BUFFER_SIZE-4 if (length-readLength)>(BUFFER_SIZE-4) else (length-readLength))
            readLength+= len(l)
        if not l:
            print("Upload Complete")
            break

def establishSendRecvConn(sock):
    global flag,recvFlag,filename
    while(flag+recvFlag != 1):
        flag = int(input("Enter 0- Receive \t 1- Send \t Press any other key to exit\n"))
        '''
            Response must be opposite of flag
            For eg, if client is sending file (flag=1), then server must send recieving flag(flag=0) which sums to 1
        '''
        print("Waiting for client's Response")
        recvFlag = int(sock.recv(4).decode('utf-8'))

        #Establish flag handshake
        sock.send(bytes(str(flag),'utf-8'))

    if(flag+recvFlag == 1):return True
    else: return False



def startServer():
    
    tcpsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    tcpsock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    tcpsock.bind((TCP_IP,TCP_PORT))

    # while True:
    tcpsock.listen(1)
    print("Waiting for incoming connections")
    (sock,(ip,port)) = tcpsock.accept()
    print(f"[CONNECTED] Welcome, {ip}:{port} !")
    try:
        retry = 1
        while(retry == 1 or retry == '1'):
            if not establishSendRecvConn(sock): return False

            if(flag == FLAG_RECV):
                filename = input("Enter full path of file to receive")
            elif flag == FLAG_SEND:
                filename = input("Enter full path of file to send")
            else:
                print("Exiting program")
                return False

            totalBytes = 0
            if flag == FLAG_RECV:
                try:
                    with open(filename,'wb') as f:
                        print("Waiting for sender")
                        msgLen = int(sock.recv(HEADER_SIZE).decode('utf-8'))
                        print(f"Total Download Size: {msgLen} bytes")
                        actSize = msgLen
                        while msgLen>0:
                            if(msgLen>BUFFER_SIZE):
                                size = BUFFER_SIZE
                            else:
                                size = msgLen
                            msgLen-=BUFFER_SIZE
                            
                            data = sock.recv(size)

                            totalBytes += len(data)
                            print(f'Downloading... {str(totalBytes):>{HEADER_SIZE}} bytes {str(totalBytes/actSize*100)}% downloaded',end='\r',flush=True)

                            f.write(data)

                    print(f"\nDownload Complete... {str(totalBytes):>{HEADER_SIZE}} bytes downloaded")
                except Exception as e:
                    print("Some error occured",e)
                    retry = input("Press 1 to send file again, press any other key to exit")
            

            elif flag == FLAG_SEND:
                try:
                    with open(filename,'rb') as f:
                        print("Waiting for reveiver")
                        msgLen = os.path.getsize(filename)
                        sock.send(bytes(f'{msgLen:<{HEADER_SIZE}}','utf-8'))
                        print(f"Total Upload Size: {msgLen} bytes")
                        actSize = msgLen
                        lock = Lock()

                        #For multithreading file sharing, divide the total file into 6 parts(for now) and call each thread for the file
                        # if(actSize > NO_OF_THREADS* BUFFER_SIZE):
                        #     threadLength = actSize//(NO_OF_THREADS-1)
                        #     extraLength = 0
                        #     threads = []
                        #     print("Inside")
                        #     if(threadLength*(NO_OF_THREADS-1) != actSize):
                        #         extraLength = 1
                        #     for i in range(NO_OF_THREADS-1):
                        #         t = Thread(target = sendFile,args=(sock,f,(i*threadLength),(i+1)*threadLength,lock,i))
                        #         t.start()
                        #         threads.append(t)
                        #     if(extraLength):
                        #         sendFile(sock,f,(NO_OF_THREADS-1)*threadLength,actSize,lock,NO_OF_THREADS)
                        #     for t in threads:
                        #         t.join()
                        # else:
                        sendFile(sock,f,0,actSize+1,lock,0)
                        
                except Exception as e:
                    print("Some error occured",e)
                    retry = input("Press 1 to send file again, press any other key to exit")
    except:
        pass
    finally:
        tcpsock.close()

if __name__ == "__main__":
    startServer()
