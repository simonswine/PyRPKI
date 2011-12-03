'''
Created on 02.12.2011

@author: christian
'''

import rpki
import rpki.x509
import socket
import pyrpki


class Roa(object):
    '''
    Represent a node in the roa tree
    '''
    prefixes = []
    signer = None
    asnum = None
    
    def __init__(self,file=None):
        '''
        Constructa
        '''
        if file:
            self.from_roa_file(file)
        else:
            pass
        
        
        
        
        pass
    
    def from_roa_file(self,file):
        self.prefixes = []
        self.asnum = None
        
        roa=rpki.x509.ROA(DER=open(file).read())
        
        (vers,asnum,ips) = roa.extract().get()

        for vers in ips:
            if vers[0] == '\x00\x01':
                af = socket.AF_INET
            elif vers[0] == '\x00\x02':
                af = socket.AF_INET6
            else:
                break  
            
            for ip in vers[1]:
                net=pyrpki.utils.ip2obj(ip[0],af=af)
                    
                if ip[1]==None:
                    mlen=net.prefixlen
                elif ip[1] >= net.prefixlen and ip[1] <= net.max_prefixlen:
                    mlen=int(ip[1]) 
                else:
                    raise ValueError('Wrong Prefix Length in Roa File')
            
                # Set Prefixes
                self.prefixes.append((net,mlen))
                self.asnum = asnum

        pass    