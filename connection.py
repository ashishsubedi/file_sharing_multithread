'''
    Author: Ashish Subedi
    File: Connection.py
    Description: Connection file with functionality of transfering file in thread safe queue


'''
from threading import Thread,Lock
import  queue
import socket, sys,os

TCP_IP = 'localhost'
TCP_PORT = 7200

BUFFER_SIZE = 1024
NO_OF_THREADS = 4
HEADER_SIZE = 10

FLAG_SEND = 1
FLAG_RECV = 0

flag = -1
recvFlag = -1
filename = ""

stopSendRecv = False

q= queue.Queue()
#TODO
# ADD client and server socket initialization here
def startServer():
    try:    
        tcpsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        tcpsock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        tcpsock.bind((TCP_IP,TCP_PORT))
    
        # while True:
        tcpsock.listen(1)
        print("Waiting for incoming connections")
        (sock,(ip,port)) = tcpsock.accept()
        print(f"[CONNECTED] Welcome, {ip}:{port} !")
        return tcpsock,sock,(ip,port)

    except Exception as e:

        print("Server starting Error:",e)

def establishSendRecvConn(sock,server=True):
    '''
        server: True if user is server
    '''
    global flag,recvFlag,filename
    while(flag+recvFlag != 1):
        flag = int(input("Enter 0- Receive \t 1- Send \t Press any other key to exit \n "))
        '''
            Response must be opposite of flag
            For eg, if client is sending file (flag=1), then server must send recieving flag(flag=0) which sums to 1
        '''
        if(server):
            print("Waiting for client's Response")
            recvFlag = int(sock.recv(4).decode('utf-8'))
        else:
            #Establish flag handshake
            sock.send(bytes(str(flag),'utf-8'))
        if(not server):
            print("Waiting for client's Response")
            recvFlag = int(sock.recv(4).decode('utf-8'))
        else:
            #Establish flag handshake
            sock.send(bytes(str(flag),'utf-8'))


    if(flag+recvFlag == 1):return True,flag
    else: return False,flag


def recvFile(sock,filename):
    global q,stopSendRecv 
    stopSendRecv = False

    msgLen = int(sock.recv(HEADER_SIZE).decode('utf-8'))
    print(f"Total Download Size: {msgLen} bytes")
    actSize = msgLen
    
    lock = Lock()
    recvThread = Thread(target=initRecv,args=(sock,lock,actSize))
    recvThread.start()
    threadLength = actSize//(NO_OF_THREADS-1)

    extraLength = 0
    threads = []
    if(threadLength*(NO_OF_THREADS-1) != actSize):
        extraLength = 1
    #Waiting till first queue is filled with data 
    while q.qsize()<2:
        pass
#TODO
#IF size is small, make singlethreaded recv
    for i in range(NO_OF_THREADS-1):
        t = Thread(target = _recv,args=(sock,filename,threadLength,q,lock))
        t.start()
        threads.append(t)

    if extraLength:
        t = Thread(target=_recv,args=(sock,filename,actSize - threadLength*(NO_OF_THREADS-1),q,lock))
        t.start()
        threads.append(t)
    #TODO
    #Join the threads and after that merge the files 
    recvThread.join()
    print('  Successfully File Downloaded')
    for t in threads:
        t.join()
    

def _recv(sock,filename,msgLen,q,lock):
    try:
        while not stopSendRecv:
            lock.acquire()
            data=q.get(True,2)
    
            i = int.from_bytes(data[0:4],'big')
            data = data[4:]
            f = open(filename+str(i),'ab')
            f.write(data)
            f.close()
            lock.release()
    except:
        lock.release()

   

def sendFile(sock,filename):
    global q,stopSendRecv
    stopSendRecv = False
    
    threads = []
    try:

        lock = Lock()
        initSendThread = Thread(target=initSend,args = (sock,lock))
        initSendThread.start()
        with open(filename,'rb') as f:
            msgLen = os.path.getsize(filename)
            sock.send(bytes(f'{msgLen:<{HEADER_SIZE}}','utf-8'))
            actSize = msgLen
            threadLength = 0
            
            extraLength = 0
            if(actSize > NO_OF_THREADS*BUFFER_SIZE):
                threadLength = actSize//(NO_OF_THREADS-1)
                if(threadLength * (NO_OF_THREADS-1) != actSize):
                    extraLength = 1

                for i in range(NO_OF_THREADS-1):
                    t = Thread(target=_sendFile, args = (sock,f,(i*threadLength),(i+1)*threadLength,lock,i,q))
                    t.start()
                    threads.append(t)
                for t in threads:
                    t.join()

            else:
                _sendFile(sock,f,0,actSize,lock,0,q)

            
       
        stopSendRecv = True

        initSendThread.join()

            #Finished I guess
            
    except Exception as e:
        print("ERROR:",e)
        sock.close()
        f.close()


        
def _sendFile(sock,f,seek,end,lock,part,q):

    while True:
        length = end-seek-1
        readLength = 0
        f.seek(seek,0)

        l = f.read(BUFFER_SIZE-4 if (length-readLength)>(BUFFER_SIZE-4) else (length-readLength))
        readLength+= len(l)

        part_byte = part.to_bytes(4,'big')
        # while the file contains data after read
        while(l):
            print(part,len(l))
            # print(f'Uploading {part}... {str(totalBytes):>{HEADER_SIZE}} bytes ',end='\r',flush=True)
            lock.acquire()
            q.put(part_byte,False)
            q.put(l,False)
            lock.release()
            if(length<readLength): return
            l = f.read(BUFFER_SIZE-4 if (length-readLength)>(BUFFER_SIZE-4) else (length-readLength))
            readLength+= len(l)
        if not l:
            print(f"Part {part} Complete")
            break

 



def initSend(sock,lock):
    '''
    Initialize queue before sending the file
    '''
    global q
    totalBytes = 0
    while not stopSendRecv:
        #queue contains in the form [part,data,part,data]

        if(q.qsize()>1):
            lock.acquire()
            sock.send(q.get(False))
            data = q.get(False)
            sock.sendall(data)
            lock.release()
            totalBytes += len(data)
            print(f"Total Uploaded: {totalBytes} uploaded",end='\r',flush=True)
    print("Upload Complete")

def initRecv(sock,lock,msgLen):

    global q,stopSendRecv
    extraBytes = 4
    totalBytes = 0
    while (msgLen>0):
        if(msgLen > (BUFFER_SIZE-extraBytes)):
    
            size = BUFFER_SIZE
        else:
            size = msgLen+extraBytes

        msgLen -= BUFFER_SIZE
        
        lock.acquire()
       
        data = sock.recv(size)

        q.put(data,False)
        lock.release()
        totalBytes += size
        print(f"Received {totalBytes} bytes of data",end='\r',flush=True)
    print("Download Complete")
    while True:
        if(q.empty()):
            stopSendRecv = True
            break


















































































































