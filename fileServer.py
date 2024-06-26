#TODO: add back shebang and give perms

# Echo server program

import socket, sys, re, os, time
sys.path.append("../lib")       # for params
from lib import params, buf

switchesVarDefaults = (
    (('-l', '--listenPort') ,'listenPort', 50001),
    (('-?', '--usage'), "usage", False), # boolean (set if present)
    )


paramMap = params.parseParams(switchesVarDefaults)

listenPort = paramMap['listenPort']
listenAddr = ''       # Symbolic name meaning all available interfaces

pidAddr = {}                    # for active connections: maps pid->client addr 

if paramMap['usage']:
    params.usage()

# server code to be run by child
def readFromClient(connAddr):  
    sock, addr = connAddr
    print(f'Child: pid={os.getpid()} connected to client at {addr}')
    contents = b''
    #Reader whole archive and store the contents in contents
    while (len(bt := sock.recv(1024)) != 0):
        contents += bt
    #while there are contents to read
    while len(contents):
        #Take first 64 bytes as set by framer and take the name out
        fileHeader = contents[:64]
        fileName = fileHeader[:32].decode().strip('\x00')
        fileName = f"src/{fileName}" 

        #Slice the last 32 bytes to get the file size
        fileSize = fileHeader[32:64].decode().strip('\x00')
        fileSize = int(fileSize)

        #Get the file contents outside of file header
        fileContents = contents[64:64+fileSize]
        #update contents
        contents = contents[64+fileSize:]

        #Write contents to file
        fd = os.open(fileName, os.O_WRONLY | os.O_CREAT)
        writer = buf.BufferedFdWriter(fd)
        for i in fileContents:
            writer.writeByte(i)
        writer.close()    
    sock.shutdown(socket.SHUT_WR)
    sys.exit(0)                 # terminate child

listenSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# listener socket will unbind immediately on close
listenSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# accept will block for no more than 5s
listenSock.settimeout(5)          
# bind listener socket to port
listenSock.bind((listenAddr, listenPort))
# set state to listen
listenSock.listen(1)              # allow only one outstanding request

# s is a factory for connected sockets
while True:
    # reap zombie children (if any)
    while pidAddr.keys():
        # Check for exited children (zombies).  If none, don't block (hang)
        if (waitResult := os.waitid(os.P_ALL, 0, os.WNOHANG | os.WEXITED)): 
            zPid, zStatus = waitResult.si_pid, waitResult.si_status
            print(f"""zombie reaped:
            \tpid={zPid}, status={zStatus}
            \twas connected to {pidAddr[zPid]}""")
            del pidAddr[zPid]
        else:
            break               # no zombies; break from loop
    print(f"Currently {len(pidAddr.keys())} clients")

    try:
        connSockAddr = listenSock.accept() # accept connection from a new client
    except TimeoutError:
        connSockAddr = None 

    if connSockAddr is None:
        continue
        
    forkResult = os.fork()     # fork child for this client 
    if (forkResult == 0):        # child
        listenSock.close()         # child doesn't need listenSock
        readFromClient(connSockAddr)
    # parent
    sock, addr = connSockAddr
    sock.close()   # parent closes its connection to client
    pidAddr[forkResult] = addr
