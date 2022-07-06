import socket 
import threading
import random
import pickle
import time
import sys

'''
do fast retransmit
'''

# get all terminal inputs globally
receiver_host_ip = sys.argv[1]
receiver_port = int(sys.argv[2])
FileToSend = sys.argv[3]
MWS = int(sys.argv[4])
MSS = int(sys.argv[5])
timeout = float(sys.argv[6])
pdrop = float(sys.argv[7])
seed  = int(sys.argv[8])
random.seed(seed)
# set up sender socket
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
ssocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# additional variables
sequenceNo = 0
acknowledgementNo = 0
segmentedFile = []
fileFullyRead = False
windowStart = 1
timer = None
wsPacketIndex = 0
t_lock = threading.Condition()
retransmitAck = 0
numsizefile = 0
dAckcount = 0
dAckNum = 0
totalDacks = 0
totalDatat = 0
totaldroppers = 0
totalretrans = 0

class DataPack:
    def __init__(self, data, seqNo, ackNo, flag = "0000"):
        #the flag has 3 bits that are in the order ack,syn,fin,data respectively.
        self.data = data
        self.seqNo = seqNo
        self.ackNo = ackNo
        self.flag = flag
        
def PacketDrop():
    rand = random.random()
    if (rand < pdrop):
        return True
    else:
        return False
        
def addLog(action, pType, logSeq, logAck, logLen):
    logTime = str(time.clock()*1000)
    tabSpace = [7,10,6,5,5,1]
    dataARGS = [action, logTime, pType, logSeq, logLen, logAck]
    addStr = " "
    j = 0
    for i in tabSpace:
        dataStr = (dataARGS[j]).ljust(i)
        addStr += dataStr
        j += 1
    addStr += "\n"
    f = open("Sender_log.txt", "a")
    f.write(addStr)
    f.close()
    
def finish():
    global sequenceNo
    global acknowledgementNo
    numsizefile = segmentedFile[-1].seqNo + len(segmentedFile[-1].data)
    synPackz = DataPack('', numsizefile, acknowledgementNo, "0010")
    ssocket.sendto(pickle.dumps(synPackz), (receiver_host_ip, receiver_port))
    addLog("snd", 'F', str(synPackz.seqNo), str(synPackz.ackNo), str(len(synPackz.data)))
    data, addr = ssocket.recvfrom(2048)
    recvPackz = pickle.loads(data)
    if (recvPackz.flag == "1010"):
        acknowledgementNo = recvPackz.seqNo + 1
        addLog("rcv", "FA", str(recvPackz.seqNo), str(recvPackz.ackNo), str(len(recvPackz.data)))
        sequenceNo = recvPackz.ackNo
        # final ack for the finish
        ackPacketsendz = DataPack('', sequenceNo, acknowledgementNo, "0010")
        ssocket.sendto(pickle.dumps(ackPacketsendz), (receiver_host_ip, receiver_port))
        addLog("snd", 'F', str(ackPacketsendz.seqNo), str(ackPacketsendz.ackNo), str(len(ackPacketsendz.data)))
        # 3-way-fin complete
    f = open("Sender_log.txt", "a")
    f.write("\n")
    f.write("Amount of Data Transferred = %s \n" % totalDatat)
    f.write("Number of Data Segments Sent (excluding retransmissions) = %s \n" % len(segmentedFile))
    f.write("Number of (all) Packets Dropped (by the PL module) = %s \n" % totaldroppers)
    f.write("Number of Retransmitted Segments because of fast retransmit = %s \n" % totalretrans)
    f.write("Number of Duplicate Acknowledgements received = %s \n" % totalDacks)
    f.close()
    
    
def segmentFile():
    global segmentedFile
    global totalDatat
    f = open(FileToSend, "r")
    dataseg = f.read(MSS)
    totalDatat += len(dataseg)
    dataSeqNum = sequenceNo
    firstDpack = DataPack(dataseg, dataSeqNum, 1, "0001")
    segmentedFile.append(firstDpack)
    fchunksize = 0
    for chunk in iter(lambda: f.read(MSS), ''):
        totalDatat += len(chunk)
        dataSeqNum += len(chunk)
        dataDpack = DataPack(chunk, dataSeqNum, 1, "0001")
        segmentedFile.append(dataDpack)
    lastElementA = segmentedFile[-1]
    lastElementA.flag = "0011"
    windowStart = segmentedFile[0].seqNo      

def recv_handler():
    global fileFullyRead
    global wsPacketIndex
    global windowStart
    global t_lock
    global dAckcount
    global dAckNum
    global totalDacks
    global totalretrans
    while (fileFullyRead == False):
        dataA, addrA = ssocket.recvfrom(2048)
        if ((ssocket.gettimeout() == None) or (ssocket.gettimeout() > 0)):
            rPack = pickle.loads(dataA)
            #FAST RETRANSMIT HANDLER
            if (rPack.ackNo == dAckNum):
                dAckcount += 1
                totalDacks += 1
            else:
                dAckcount = 1
                dAckNum = rPack.ackNo
            #fast retrasmit condition below
            if (dAckcount == 3):
                totalretrans += 1
                sendwindowpackets(windowStart, wsPacketIndex)   #fast retransmit happens
            if (rPack.flag == "1111"):
                fileFullyRead = True
            else:
                addLog("rcv", "R", str(rPack.seqNo), str(rPack.ackNo), str(len(rPack.data)))
                with t_lock:
                    #update vars wsPacketIndex and windowStart
                    i = 0
                    while (i < len(segmentedFile)):
                        if (segmentedFile[i].seqNo == rPack.ackNo):
                            wsPacketIndex = i
                            windowStart = segmentedFile[i].seqNo 
                            break
                        i+=1
                    t_lock.notify()
        else:
            # RETRANSMIT IF TIMEOUT HAPPENS
            sendwindowpackets(windowStart, wsPacketIndex)
        
def sendwindowpackets(ws, i):
    global totaldroppers
    wsindex = i
    while((segmentedFile[wsindex].seqNo + len(segmentedFile[wsindex].data)) <= (ws+MWS+1)):
        if (PacketDrop() == False):
            ssocket.sendto(pickle.dumps(segmentedFile[wsindex]), (receiver_host_ip, receiver_port))
            addLog("snd", 'D', str(segmentedFile[wsindex].seqNo), str(segmentedFile[wsindex].ackNo), str(len(segmentedFile[wsindex].data)))
        else:
            totaldroppers += 1
            addLog("drop", 'D', str(segmentedFile[wsindex].seqNo), str(segmentedFile[wsindex].ackNo), str(len(segmentedFile[wsindex].data)))
        #set timer when wsindex = i
        if (wsindex == i):
            ssocket.settimeout(timeout)
        if ((wsindex+1) < len(segmentedFile)):
            wsindex+=1
        else: 
            break
    
def dataTransmission():
    global windowStart
    global fileFullyRead
    global wsPacketIndex
    global t_lock
    recv_thread=threading.Thread(name="RecvHandler", target=recv_handler)
    recv_thread.daemon=True
    recv_thread.start()
    while (not fileFullyRead):
        sendwindowpackets(windowStart, wsPacketIndex)
        time.sleep(1)  #need this sleep so the sending window can be adjusted without wasting resources.
    finish()
        
def handshake():
    global sequenceNo
    global acknowledgementNo
    # create and send an empty syn packet
    synPack = DataPack('', sequenceNo, acknowledgementNo, "0100")
    ssocket.sendto(pickle.dumps(synPack), (receiver_host_ip, receiver_port))
    addLog("snd", 'S', str(synPack.seqNo), str(synPack.ackNo), str(len(synPack.data)))
    # now we need to recieve the syn-ack
    data, addr = ssocket.recvfrom(2048)
    recvPack = pickle.loads(data)
    if (recvPack.flag == "1100"):
        acknowledgementNo = recvPack.seqNo + 1
        addLog("rcv", "SA", str(recvPack.seqNo), str(recvPack.ackNo), str(len(recvPack.data)))
        sequenceNo += 1
        # final ack for the handshake
        ackPacketsend = DataPack('', sequenceNo, acknowledgementNo, "1000")
        ssocket.sendto(pickle.dumps(ackPacketsend), (receiver_host_ip, receiver_port))
        addLog("snd", 'A', str(ackPacketsend.seqNo), str(ackPacketsend.ackNo), str(len(ackPacketsend.data)))
        # 3-way-handshake complete

def handle_client():
    handshake()
    segmentFile()
    dataTransmission()

if __name__ == "__main__":
    # make log file empty
    open("Sender_log.txt", 'w').close()
    handle_client()