from socket import *
import pickle
import time
import sys
import operator

receiver_port = int(sys.argv[1])
FileReceived = sys.argv[2]
sequenceNo = 0
acknowledgementNo = 0
ssocket = socket(AF_INET, SOCK_DGRAM)
ssocket.bind(('localhost', receiver_port))
packetBuffer= []
nextSequence = 0
totalDataAmt = 0
totalDupers = 0



class DataPack:
    def __init__(self, data, seqNo, ackNo, flag = "0000"):
        #the flag has 3 bits that are in the order ack,syn,fin,data respectively.
        self.data = data
        self.seqNo = seqNo
        self.ackNo = ackNo
        self.flag = flag
        
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
    f = open("Receiver_log.txt", "a")
    f.write(addStr)
    f.close()
    
def finish():
    global sequenceNo
    global acknowledgementNo
    global nextSequence
    global totalDataAmt
    while(True):
        message, clientAddress = ssocket.recvfrom(2048)
        msgPackz = pickle.loads(message)
        if (msgPackz.flag == "0010"):
            break
    #acknowledgementNo += 1
    addLog("rcv", 'F', str(msgPackz.seqNo), str(msgPackz.ackNo), str(len(msgPackz.data)))
    if (msgPackz.flag == "0010"):
        synackPackz = DataPack('', sequenceNo, acknowledgementNo, "1010")
        ssocket.sendto(pickle.dumps(synackPackz), clientAddress)
        sequenceNo += 1
        addLog("snd", 'FA', str(synackPackz.seqNo), str(synackPackz.ackNo), str(len(synackPackz.data)))
        messageA, clientAddressA = ssocket.recvfrom(2048)
        ackmsgPackz = pickle.loads(messageA)
        addLog("rcv", 'F', str(ackmsgPackz.seqNo), str(ackmsgPackz.ackNo), str(len(ackmsgPackz.data)))
    #write to outputfile
    f = open("FileReceived.txt", "w")
    for i in packetBuffer:
        totalDataAmt += len(i.data)
        f.write(i.data)
    f.close()
    g = open("Receiver_log.txt", "a")
    g.write("\n")
    g.write("Amount of (original) Data Received (in bytes) = %s \n" % totalDataAmt)
    g.write("Number of (original) Data Segments Received = %s \n" % len(packetBuffer))
    g.write("Number of duplicate segments received = %s \n" % totalDupers)
    g.close()
    
    #add extra deets
        
def handshake():
    global sequenceNo
    global acknowledgementNo
    global nextSequence
    message, clientAddress = ssocket.recvfrom(2048)
    msgPack = pickle.loads(message)
    acknowledgementNo += 1
    addLog("rcv", 'S', str(msgPack.seqNo), str(msgPack.ackNo), str(len(msgPack.data)))
    if (msgPack.flag == "0100"):
        synackPack = DataPack('', sequenceNo, acknowledgementNo, "1100")
        ssocket.sendto(pickle.dumps(synackPack), clientAddress)
        sequenceNo += 1
        addLog("snd", 'SA', str(synackPack.seqNo), str(synackPack.ackNo), str(len(synackPack.data)))
        messageA, clientAddressA = ssocket.recvfrom(2048)
        ackmsgPack = pickle.loads(messageA)
        addLog("rcv", 'A', str(ackmsgPack.seqNo), str(ackmsgPack.ackNo), str(len(ackmsgPack.data)))
        nextSequence = ackmsgPack.seqNo
            
def checkAllRecieved():
    i = 0
    while (i < len(packetBuffer)):
        if (packetBuffer[i].flag == "0011"):
            return True
        if (i == len(packetBuffer)-1):
            return False
        if ((packetBuffer[i].seqNo + len(packetBuffer[i].data)) == (packetBuffer[i+1]).seqNo):
            i += 1
        else:
            return False

def checkmsginbuffer(seqnoo):
    for i in packetBuffer:
        if (i.seqNo == seqnoo):
            return True
    return False
    
def receiveData():
    global nextSequence
    global packetBuffer 
    global totalDupers
    message, clientAddress = ssocket.recvfrom(2048)
    msgpack = pickle.loads(message)
    addLog("rcv", 'D', str(msgpack.seqNo), str(msgpack.ackNo), str(len(msgpack.data)))
    packetBuffer.append(msgpack)
    conn = True
    while (conn == True):
        if (checkmsginbuffer(msgpack.seqNo) == False):
            packetBuffer.append(msgpack)
            packetBuffer.sort(key=operator.attrgetter('seqNo')) #sort the buffer
        else:
            totalDupers += 1
        if (nextSequence == msgpack.seqNo):
            i = 0
            while (i < len(packetBuffer)):
                if (i == len(packetBuffer)-1):
                    break
                if ((packetBuffer[i].seqNo + len(packetBuffer[i].data)) == packetBuffer[i+1].seqNo):
                    i += 1
                else:
                    break
            nextSequence = packetBuffer[i].seqNo + len(packetBuffer[i].data)
            requestData = DataPack('', 1, nextSequence, "0100")
            ssocket.sendto(pickle.dumps(requestData), clientAddress)
            addLog("snd", 'A', str(requestData.seqNo), str(requestData.ackNo), str(len(requestData.data)))
        else:
            # resend that ack
            requestDataa = DataPack('', 1, nextSequence, "0100")
            ssocket.sendto(pickle.dumps(requestDataa), clientAddress)
            addLog("snd", 'A', str(requestDataa.seqNo), str(requestDataa.ackNo), str(len(requestDataa.data)))
        if (checkAllRecieved() == True):
            requestDat = DataPack('', 0, 0, "1111")
            ssocket.sendto(pickle.dumps(requestDat), clientAddress)
            conn = False
        if (conn == True):
            message, clientAddress = ssocket.recvfrom(2048)
            msgpack = pickle.loads(message)
            addLog("rcv", 'D', str(msgpack.seqNo), str(msgpack.ackNo), str(len(msgpack.data)))

def start():
    handshake()
    receiveData()
    finish()
        
if __name__ == "__main__":
    # make log file empty
    open("FileReceived.txt", 'w').close()
    open("Receiver_log.txt", 'w').close()
    start()