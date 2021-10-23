import socket
hostname = socket.gethostname()
if 'rasp' in hostname:
    print ('raspi')
else:
    pass