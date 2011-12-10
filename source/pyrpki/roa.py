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

    def __init__(self,file=None):
        '''
        Constructa
        '''
        self.prefixes = []
        self.signer =  None
        self.asnum = None
        
        
        if file:
            self.from_roa_file(file)
        else:
            pass
        
        
        
        
        pass
    
    def set_as(self,asnum):
        self.asnum = asnum
    
    def add_prefix(self,prefix,max_len=None):
        
        if max_len == None:
            max_len = prefix.prefixlen
        elif prefix.prefixlen > max_len or prefix.max_prefixlen < max_len:
            raise ValueError('Falsche Prefixlaenge')
        self.prefixes.append((prefix,max_len))
    
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
                self.add_prefix(prefix=net,max_len=mlen)
                self.asnum = asnum

        pass    