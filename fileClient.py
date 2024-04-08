#TODO: add back shebang and give perms

# Echo client program
import socket, sys, re, os
sys.path.append("../lib")       # for params
from lib import params,buf

switchesVarDefaults = (
    (('-s', '--server'), 'server', "127.0.0.1:50001"),
    (('-?', '--usage'), "usage", False), # boolean (set if present)
    )


progname = "framedClient"
paramMap = params.parseParams(switchesVarDefaults)
server,usage =  paramMap["server"], paramMap["usage"]

if usage:
    params.usage()

try:
    serverHost, serverPort = re.split(":", server)
    serverPort = int(serverPort)
except:
    print("Can't parse server:port from '%s'" % server)
    sys.exit(1)

s = None
for res in socket.getaddrinfo(serverHost, serverPort, socket.AF_UNSPEC, socket.SOCK_STREAM):
    af, socktype, proto, canonname, sa = res
    try:
        print("creating sock: af=%d, type=%d, proto=%d" % (af, socktype, proto))
        s = socket.socket(af, socktype, proto)
    except socket.error as msg:
        print(" error: %s" % msg)
        s = None
        continue
    try:
        print(" attempting to connect to %s" % repr(sa))
        s.connect(sa)
    except socket.error as msg:
        print(" error: %s" % msg)
        s.close()
        s = None
        continue
    break

if s is None:
    print('could not open socket')
    sys.exit(1)



#Initialize where the full data to be written will be stored
while True:
    fileList = input("enter files to send (enter \"stop\" to end stream): ")
    fileList = fileList.split()
    if "stop" in fileList:
        break
    archive = b''
    for file in fileList:
        curFile = os.open(file,os.O_RDONLY)
        reader = buf.BufferedFdReader(curFile)
        file_size = os.path.getsize(file)

        #Create a fileHeader to store the file name/path and the file size
        fileHeader = bytearray(64)
        for i in range(len(file)):
            fileHeader[i] = file[i].encode()[0]
        for i in range(len(str(file_size))):
            fileHeader[i+32]= str(file_size)[i].encode()[0]#store file size 32 bytes later in header

        #read through file and store contents in array
        bt = reader.readByte()
        content = []
        while bt is not None:
            content.append(bt)
            bt = reader.readByte()
        reader.close()
        #Store both file header and contents casted as a byte array in fileContents
        #store complete file data in archive then loop
        fileContents = fileHeader+ bytearray(content)
        archive += fileContents
    s.send(archive) #send total bytes
s.shutdown(socket.SHUT_WR)    
s.close()

'''

outMessage = "".encode()
s.send(outMessage)

while len(outMessage):
    print("sending '%s'" % outMessage.decode())
    bytesSent = os.write(s.fileno(), outMessage)
    outMessage = outMessage[bytesSent:]

data = os.read(s.fileno(), 1024).decode()
print("Received '%s'" % data)

outMessage = "Hello world!".encode()
while len(outMessage):
    print("sending '%s'" % outMessage.decode())
    bytesSent = s.send(outMessage)
    outMessage = outMessage[bytesSent:]

s.shutdown(socket.SHUT_WR)      # no more output

while 1:
    data = s.recv(1024).decode()
    print("Received '%s'" % data)
    if len(data) == 0:
        break
print("Zero length read.  Closing")

s.close()
'''