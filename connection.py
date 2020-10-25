'''
    Author: Ashish Subedi
    File: Connection.py
    Description: Connection file with functionality of transfering file in thread safe queue


'''
import threading, queue
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

q= queue.Queue()

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


def recvFile(sock,msgLen,lock,q):
    extraBytes = 4
    totalBytes = 0
    '''
    while msgLen>0:
        if(msgLen>(BUFFER_SIZE-extraBytes)):
            size = BUFFER_SIZE
        else:
            size = msgLen+extraBytes

        msgLen-=BUFFER_SIZE
        lock.acquire()
        data = sock.recv(size)
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
'''



def sendFile(sock,filename):
    global q
    try:
        sendQueueThread = Thread(target=initSend,args = (sock))
        with open(filename,'rb') as f:
            msgLen = os.path.getsize(filename)
            actSize = msgLen
            lock = Lock()
            
            if(actSize > NO_OF_THREADS*BUFFERSIZE):
                threadLength = actSize//(NO_OF_THREADS-1)
                extraLength = 0
                threads = []
                if(threadLength * (NO_OF_THREADS-1) != actSize):
                    extraLength = 1

            for i in range(NO_OF_THREADS-1):
                t = Thread(target=_sendFile, args = (sock,f,(i*threadLength),(i+1)*threadLength,lock,i,q))
                t.start()
                threads.append(t)
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
        # totalBytes = 0
        while(l):
            # totalBytes += len(l)
            print(part,len(part_byte),len(l))
            # print(f'Uploading {part}... {str(totalBytes):>{HEADER_SIZE}} bytes ',end='\r',flush=True)
            lock.acquire()
            q.put(part_byte,False)
            q.put(l,False)
            lock.release()
            if(length<readLength): return
            l = f.read(BUFFER_SIZE-4 if (length-readLength)>(BUFFER_SIZE-4) else (length-readLength))
            readLength+= len(l)
        if not l:
            print("Part  Complete")
            break

 



def iniSend(sock,lock):
    '''
    Initialize queue before sending the file
    '''
    global q
    while True:
        #queue contains in the form [part,data,part,data]
        if(len(q)>1):
            lock.acquire()
            q.send(q.get(False))
            q.sendall(q.get(False))
            lock.release()
























,

























,

























,

























,
        

























,
