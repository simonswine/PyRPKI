'''
Created on 02.12.2011

@author: christian
'''

import ipaddr
import datetime

class RoaNode(object):
    '''
    Represent a node in the roa tree
    '''
    #prefix = None
    #parent = None
    #childs = []
    #roas = []
    ip_version = 4

    
    def __init__(self,prefix=None):
        '''
        Constructa
        '''
        # Instanciate Attributes
        
        self.parent = None
        self.roas = []
        self.childs = set()
        
        if prefix==None:
            self.prefix = ipaddr.IPv4Network('0.0.0.0/0')
        self.prefix = prefix
        
        self.check()
            
        pass
    
    def add_prefix(self,prefix):
         
        
        if self.prefix.version != prefix.version:
            raise ValueError("Address Families doesn't match")
        
        if not self.prefix.Contains(prefix) or self.prefix.prefixlen == prefix.prefixlen:
            raise ValueError('My Prefix does not contain the given Prefix')
        
        ch_res={
                'dup' : [],
                'contains' : [],
                'contained' : [],
                }
        
        for c in self.childs:
            if c.prefix == prefix:
                ch_res['dup'].append(c)
            elif c.prefix.Contains(prefix):
                ch_res['contained'].append(c)
            elif prefix.Contains(c.prefix):
                ch_res['contains'].append(c)

        if ch_res['dup'] == [] and ch_res['contained'] == []:
            """Nicht vorhanden und nicht teil eines Childs"""
            me=RoaNode(prefix=prefix)
            self.childs.add(me)
            
            if len(ch_res['contains']) > 0:
                """Enthaelt andere Childs"""
                for c in ch_res['contains']:
                    self.childs.discard(c)
                    me.childs.add(c)
              
            
        elif ch_res['dup'] != []:
            """Duplikat"""
            pass
        elif len(ch_res['contained']) == 1:
            """Enthalten in genau einem Child"""
            ch_res['contained'][0].add_prefix(prefix=prefix)
        
        else:
            raise NotImplementedError('Nicht implementier Fall')
        
        pass
    
    def add_local_roa(self,roa):
        
        for prefix in roa.prefixes:
            if self.prefix == prefix[0]:

                self.roas.append(roa)
                
                
        
    def add_roa(self,roa):
        
        for prefix in roa.prefixes:
            if prefix[0].version == self.prefix.version:
                node=self.get_prefix(prefix=prefix[0])
                if node == None:
                    self.add_prefix(prefix=prefix[0])
                    node=self.get_prefix(prefix=prefix[0])    
                node.add_local_roa(roa)
                
    def get_prefix(self, prefix):
        
        if self.prefix.Contains(prefix):
            if self.prefix == prefix:
                return self
            for c in self.childs:
                p = c.get_prefix(prefix=prefix)
                if p != None:
                    return p
            
        return None
    
    def ancestors(self):
        
        c_sum =0
        for c in self.childs:
            c_sum += c.ancestors()
        
        return len(self.childs) + c_sum
        
    def show_filter_rules(self,type='cisco_more_specific',level=0,roa_parent=False):
        
        roa_parent_c=roa_parent
        if len(self.roas) > 0:
            roa_parent_c=True
            
        
        rules = []
        for c in self.childs:
            rules +=(c.show_filter_rules(level=level+1,roa_parent=roa_parent_c))
        
        
        
        max_len = self.prefix.prefixlen
        asnums = []
        for roa in self.roas:
            # Adding AS Num
            if roa.asnum not in asnums:
                asnums.append(roa.asnum)
                
            # Checking Prefix Lengths
            for prefix in roa.prefixes:
                if prefix[0] == self.prefix:
                    if   prefix[1] > max_len:
                        max_len =  prefix[1]
        
        if len(self.roas) > 0:
            
            # Baue Regel fuer eigene ROAs
            
            
            # Kommentar
            rules.append("! Prefix %s bis /%d Origins: %s" % (self.prefix,max_len,','.join(['AS'+str(i) for i in asnums])))
            # Erlaubt
            if roa_parent:
                if max_len == self.prefix.prefixlen:
                    rules.append("#PREFIXLIST# deny %s" % (self.prefix))            
                else:
                    rules.append("#PREFIXLIST# deny %s le %d" % (self.prefix,max_len))
            # Verbot
            if max_len < self.prefix.max_prefixlen:
                rules.append("#PREFIXLIST# permit %s ge %d" % (self.prefix,max_len+1))
            
        # Erster Aufruf     
        if level == 0:
            if self.prefix.version == 4:
                command_prefix = 'ip'
            elif self.prefix.version == 6:
                command_prefix = 'ipv6'
            i=1000
            rules_proc=['! DATA from RPKI validated at lrz.de, LAST UPDATE: %s'% datetime.datetime.now()]
            for line in rules:
                if not line.find('#PREFIXLIST#'):
                    i+=5
                    line = line.replace("#PREFIXLIST#","%s prefix-list ROA_FILTER seq %s" % (command_prefix,i))
                rules_proc.append(line)
            
            return "\n".join(rules_proc)
            
        else:
            return rules

    
    
    def check(self):
        
        for c in self.childs:
            
            assert self.prefix.prefixlen < c.prefix.prefixlen
            assert self.prefix.Contains(c.prefix) == True
            
            c.check()
        
        pass
    
    def __str__(self):
        rstr = '| %s Childs:%d Roas:%d' % (self.prefix.__str__(),len(self.childs),len(self.roas))
        
        for c in self.childs:
            for l in c.__str__().split('\n'):     
                rstr += '\n| %s' % (l)
                    
        return  rstr
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)
        