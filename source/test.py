
import pyrpki
import socket

# Testing Nodes
"""
root = pyrpki.RoaNode(prefix=ipaddr.IPNetwork('0.0.0.0/0'))

root.childs.append(pyrpki.RoaNode(prefix=ipaddr.IPNetwork('1.0.0.0/8')))
root.childs.append(pyrpki.RoaNode(prefix=ipaddr.IPNetwork('2.0.0.0/8')))
root.childs.append(pyrpki.RoaNode(prefix=ipaddr.IPNetwork('3.0.0.0/8')))
root.childs.append(pyrpki.RoaNode(prefix=ipaddr.IPNetwork('5.0.0.0/8')))


t1 = pyrpki.RoaNode(prefix=ipaddr.IPNetwork('4.0.0.0/8'))
t1.childs.append(pyrpki.RoaNode(prefix=ipaddr.IPNetwork('4.1.0.0/16')))
t1.childs.append(pyrpki.RoaNode(prefix=ipaddr.IPNetwork('4.2.0.0/16')))
t2 = pyrpki.RoaNode(prefix=ipaddr.IPNetwork('4.3.0.0/16'))
t2.childs.append(pyrpki.RoaNode(prefix=ipaddr.IPNetwork('5.3.2.0/24')))
t1.childs.append(t2)


root.childs.append(t1)

root.check()

print root"""

"""
root = pyrpki.RoaNode(prefix=ipaddr.IPNetwork('0.0.0.0/0'))

root.add_prefix(prefix=ipaddr.IPNetwork('1.0.0.0/8'))
root.add_prefix(prefix=ipaddr.IPNetwork('1.0.0.0/8'))
root.add_prefix(prefix=ipaddr.IPNetwork('1.0.0.0/8'))
root.add_prefix(prefix=ipaddr.IPNetwork('1.2.0.0/16'))
root.add_prefix(prefix=ipaddr.IPNetwork('1.3.0.0/16'))
root.add_prefix(prefix=ipaddr.IPNetwork('1.0.0.0/9'))
root.add_prefix(prefix=ipaddr.IPNetwork('0.0.0.0/2'))
roa = pyrpki.Roa()
roa.set_as(1234)
roa.add_prefix(prefix=ipaddr.IPNetwork('1.3.0.0/16'),max_len=32)

root.add_roa(roa)
print root
"""

