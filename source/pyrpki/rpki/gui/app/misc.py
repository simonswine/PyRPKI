# $Id: misc.py 3415 2010-07-16 22:59:26Z melkins $
"""
Copyright (C) 2010  SPARTA, Inc. dba Cobham Analytic Solutions

Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND SPARTA DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS.  IN NO EVENT SHALL SPARTA BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
"""

import rpki.resource_set
import rpki.ipaddrs

def str_to_range(lo, hi):
    """Convert IP address strings to resource_range_ip."""
    x = rpki.ipaddrs.parse(lo)
    y = rpki.ipaddrs.parse(hi)
    assert type(x) == type(y)
    if isinstance(x, rpki.ipaddrs.v4addr):
        return rpki.resource_set.resource_range_ipv4(x, y)
    else:
        return rpki.resource_set.resource_range_ipv6(x, y)

def parse_resource_range(s):
    '''Parse an IPv4/6 resource range.'''
    # resource_set functions only accept str
    if isinstance(s, unicode):
        s = s.encode()
    try:
        return rpki.resource_set.resource_range_ipv4.parse_str(s)
    except ValueError:
        return rpki.resource_set.resource_range_ipv6.parse_str(s)

def top_parent(prefix):
    '''Returns the topmost resource from which the specified argument derives'''
    while prefix.parent:
        prefix = prefix.parent
    return prefix

# vim:sw=4 ts=8 expandtab
