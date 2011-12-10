from pyrpki.roanode import RoaNode
import ipaddr

import rpki
import os.path
from roa import Roa
import socket


def parse_roas(roa_files):
    roas=[]
    #TODO: remove limit 
    for file in roa_files:
        roas.append(Roa(file=file))
        
        #break
    
    return roas

def ip2obj(ip,af='inet'):
    
    length={
           socket.AF_INET  : 32,
           socket.AF_INET6 : 128,          
           }
    
    
    if length.has_key(af):
 
        prefix_len=len(ip)
        
        byte_ip=''
        byte=''
        for i in range(length[af]):
            try:
                byte += str(ip[i])
            except IndexError:
                byte += '0'
            if len(byte) == 8:
                byte_ip += chr(int(byte,2)) 
                byte = ''

        netstring = '%s/%d' % (socket.inet_ntop(af, byte_ip), prefix_len)
        net = ipaddr.IPNetwork(netstring)

        return net
               
    else:
        raise ValueError('Wrong AF')


def get_roa_tree(dir='/var/rcynic/data/authenticated/'):
    
    tree = {
            socket.AF_INET : RoaNode(prefix=ipaddr.IPv4Network('0.0.0.0/0')),
            socket.AF_INET6 : RoaNode(prefix=ipaddr.IPv6Network('::/0'))
            } 
    
    rpki_files={}

    for root, dirs, files in os.walk(dir):
        for f in files:
                    
            filename_parts = f.split('.')
            
            if len(filename_parts) > 1:
                path = os.path.join(root, f)
                ext = filename_parts[-1].lower()
                
                try:
                    rpki_files[ext].append(path)
                except KeyError:
                    rpki_files[ext] = [path]
                    
    roas = parse_roas(rpki_files['roa'])
    
    for roa in roas:
        tree[socket.AF_INET].add_roa(roa)
        tree[socket.AF_INET6].add_roa(roa)
        
    return tree