from pyrpki.roanode import RoaNode
import ipaddr

import rpki
import os.path
from roa import Roa
import socket


def parse_roas(roa_files):
    roas=[]
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
    
    # Generate Prefix Tables
    prefix_table = {
                    socket.AF_INET : {},
                    socket.AF_INET6 : {},
                    }
    
    
    for roa in roas:
        for prefix in roa.prefixes:
            af = None
            if prefix[0].version == 4:
                af = socket.AF_INET
            elif prefix[0].version == 6:
                af = socket.AF_INET6
            try:
                prefix_table[af][prefix[0]].append(roa)
            except KeyError:
                prefix_table[af][prefix[0]]=[roa]
                
    for af in prefix_table:
                
        for prefix in prefix_table[af]:
            
            parents = 0
            for check_prefix in prefix_table[af]:
                if check_prefix != prefix and check_prefix.Contains(prefix) != False:
                    parents += 1    


            if parents == 0:
                tree[af].childs.append(RoaNode(prefix=ipaddr.IPv4Network('0.0.0.0/0')))
                #print prefix,parents
            
    
    #print len(roas)
    
    return tree