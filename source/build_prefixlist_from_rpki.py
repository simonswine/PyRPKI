import pyrpki
import socket

# Fetch Authenticated ROAs and build prefix list...
tree=pyrpki.get_roa_tree(dir='/home/christian/authenticated/')

print tree[socket.AF_INET].show_filter_rules()
print tree[socket.AF_INET6].show_filter_rules()

