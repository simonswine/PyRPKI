
import pyrpki
import socket


#print pyrpki.utils.ip2obj((1,1,1,0,1,1,0,0,0,0,0,0,0,0,0,0,1), af=socket.AF_INET6)

tree=pyrpki.get_roa_tree(dir='/home/christian/authenticated/')
print tree 