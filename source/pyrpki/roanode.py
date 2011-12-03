'''
Created on 02.12.2011

@author: christian
'''

import ipaddr

class RoaNode(object):
    '''
    Represent a node in the roa tree
    '''
    prefix = None
    parent = None
    childs = []
    roas = []
    ip_version = 4


    def __init__(self,prefix=None):
        '''
        Constructa
        '''
        if prefix==None:
            self.prefix = ipaddr.IPv4Network('0.0.0.0/0')
        self.prefix = prefix

        self.check()
            
        pass
    
    def check(self):
       
        
        pass
    
    def __str__(self):
        return  self.prefix.__str__()
        