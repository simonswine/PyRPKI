"""
Classes dealing with sets of resources.

The basic mechanics of a resource set are the same for any of the
resources we handle (ASNs, IPv4 addresses, or IPv6 addresses), so we
can provide the same operations on any of them, even though the
underlying details vary.

We also provide some basic set operations (union, intersection, etc).

$Id: resource_set.py 3688 2011-02-24 00:00:05Z melkins $

Copyright (C) 2009--2010  Internet Systems Consortium ("ISC")

Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND ISC DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS.  IN NO EVENT SHALL ISC BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.

Portions copyright (C) 2007--2008  American Registry for Internet Numbers ("ARIN")

Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND ARIN DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS.  IN NO EVENT SHALL ARIN BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
"""

import re, math
import rpki.ipaddrs, rpki.oids, rpki.exceptions

## @var inherit_token
# Token used to indicate inheritance in read and print syntax.

inherit_token = "<inherit>"

re_asn_range          = re.compile("^([0-9]+)-([0-9]+)$")
re_address_range      = re.compile("^([0-9:.a-fA-F]+)-([0-9:.a-fA-F]+)$")
re_prefix_with_maxlen = re.compile("^([0-9:.a-fA-F]+)/([0-9]+)-([0-9]+)$")
re_prefix             = re.compile("^([0-9:.a-fA-F]+)/([0-9]+)$")

class resource_range(object):
  """
  Generic resource range type.  Assumes underlying type is some kind
  of integer.

  This is a virtual class.  You probably don't want to use this type
  directly.
  """

  def __init__(self, min, max):
    """
    Initialize and sanity check a resource_range.
    """
    assert min.__class__ is max.__class__, "Type mismatch, %r doesn't match %r" % (min.__class__, max.__class__)
    assert min <= max, "Mis-ordered range: %s before %s" % (min, max)
    self.min = min
    self.max = max

  def __cmp__(self, other):
    """
    Compare two resource_range objects.
    """
    assert self.__class__ is other.__class__, "Type mismatch, comparing %r with %r" % (self.__class__, other.__class__)
    return cmp(self.min, other.min) or cmp(self.max, other.max)

class resource_range_as(resource_range):
  """
  Range of Autonomous System Numbers.

  Denotes a single ASN by a range whose min and max values are
  identical.
  """

  ## @var datum_type
  # Type of underlying data (min and max).

  datum_type = long

  def __str__(self):
    """
    Convert a resource_range_as to string format.
    """
    if self.min == self.max:
      return str(self.min)
    else:
      return str(self.min) + "-" + str(self.max)

  def to_rfc3779_tuple(self):
    """
    Convert a resource_range_as to tuple format for RFC 3779 ASN.1 encoding.
    """
    if self.min == self.max:
      return ("id", self.min)
    else:
      return ("range", (self.min, self.max))

  @classmethod
  def parse_str(cls, x):
    """
    Parse ASN resource range from text (eg, XML attributes).
    """
    r = re_asn_range.match(x)
    if r:
      return cls(long(r.group(1)), long(r.group(2)))
    else:
      return cls(long(x), long(x))

  @classmethod
  def from_strings(cls, a, b = None):
    """
    Construct ASN range from strings.
    """
    if b is None:
      b = a
    return cls(long(a), long(b))

class resource_range_ip(resource_range):
  """
  Range of (generic) IP addresses.

  Prefixes are converted to ranges on input, and ranges that can be
  represented as prefixes are written as prefixes on output.

  This is a virtual class.  You probably don't want to use it
  directly.
  """

  def prefixlen(self):
    """
    Determine whether a resource_range_ip can be expressed as a
    prefix.  Returns prefix length if it can, otherwise raises
    MustBePrefix exception.
    """
    mask = self.min ^ self.max
    if self.min & mask != 0:
      raise rpki.exceptions.MustBePrefix
    prefixlen = self.datum_type.bits
    while mask & 1:
      prefixlen -= 1
      mask >>= 1
    if mask:
      raise rpki.exceptions.MustBePrefix
    return prefixlen

  # Backwards compatability, will go away at some point
  _prefixlen = prefixlen

  def __str__(self):
    """
    Convert a resource_range_ip to string format.
    """
    try:
      return str(self.min) + "/" + str(self.prefixlen())
    except rpki.exceptions.MustBePrefix:
      return str(self.min) + "-" + str(self.max)

  def to_rfc3779_tuple(self):
    """
    Convert a resource_range_ip to tuple format for RFC 3779 ASN.1
    encoding.
    """
    try:
      return ("addressPrefix", _long2bs(self.min, self.datum_type.bits,
                                        prefixlen = self.prefixlen()))
    except rpki.exceptions.MustBePrefix:
      return ("addressRange", (_long2bs(self.min, self.datum_type.bits, strip = 0),
                               _long2bs(self.max, self.datum_type.bits, strip = 1)))

  @classmethod
  def parse_str(cls, x):
    """
    Parse IP address range or prefix from text (eg, XML attributes).
    """
    r = re_address_range.match(x)
    if r:
      return cls(cls.datum_type(r.group(1)), cls.datum_type(r.group(2)))
    r = re_prefix.match(x)
    if r:
      return cls.make_prefix(cls.datum_type(r.group(1)), int(r.group(2)))
    raise rpki.exceptions.BadIPResource, 'Bad IP resource "%s"' % (x)

  @classmethod
  def make_prefix(cls, prefix, prefixlen):
    """
    Construct a resource range corresponding to a prefix.
    """
    assert isinstance(prefix, cls.datum_type) and isinstance(prefixlen, (int, long))
    assert prefixlen >= 0 and prefixlen <= cls.datum_type.bits, "Nonsensical prefix length: %s" % prefixlen
    mask = (1 << (cls.datum_type.bits - prefixlen)) - 1
    assert (prefix & mask) == 0, "Resource not in canonical form: %s/%s" % (prefix, prefixlen)
    return cls(cls.datum_type(prefix), cls.datum_type(prefix | mask))

  def chop_into_prefixes(self, result):
    """
    Chop up a resource_range_ip into ranges that can be represented as
    prefixes.
    """
    try:
      self.prefixlen()
      result.append(self)
    except rpki.exceptions.MustBePrefix:
      min = self.min
      max = self.max
      while max >= min:
        bits = int(math.log(max - min + 1, 2))
        while True:
          mask = ~(~0 << bits)
          assert min + mask <= max
          if min & mask == 0:
            break
          assert bits > 0
          bits -= 1
        result.append(self.make_prefix(min, self.datum_type.bits - bits))
        min = self.datum_type(min + mask + 1)

  @classmethod
  def from_strings(cls, a, b = None):
    """
    Construct IP address range from strings.
    """
    if b is None:
      b = a
    a = rpki.ipaddrs.parse(a)
    b = rpki.ipaddrs.parse(b)
    if a.__class__ is not b.__class__:
      raise TypeError
    if cls is resource_range_ip:
      if isinstance(a, rpki.ipaddrs.v4addr):
        return resource_range_ipv4(a, b)
      if isinstance(a, rpki.ipaddrs.v6addr):
        return resource_range_ipv6(a, b)
    elif isinstance(a, cls.datum_type):
      return cls(a, b)
    raise TypeError

class resource_range_ipv4(resource_range_ip):
  """
  Range of IPv4 addresses.
  """

  ## @var datum_type
  # Type of underlying data (min and max).

  datum_type = rpki.ipaddrs.v4addr

class resource_range_ipv6(resource_range_ip):
  """
  Range of IPv6 addresses.
  """

  ## @var datum_type
  # Type of underlying data (min and max).

  datum_type = rpki.ipaddrs.v6addr

def _rsplit(rset, that):
  """
  Utility function to split a resource range into two resource ranges.
  """
  this = rset.pop(0)
  cell_type = type(this.min)
  assert type(this) is type(that) and type(this.max) is cell_type and \
         type(that.min) is cell_type and type(that.max) is cell_type
  if this.min < that.min:
    rset.insert(0, type(this)(this.min, cell_type(that.min - 1)))
    rset.insert(1, type(this)(that.min, this.max))
  else:
    assert this.max > that.max
    rset.insert(0, type(this)(this.min, that.max))
    rset.insert(1, type(this)(cell_type(that.max + 1), this.max))

class resource_set(list):
  """
  Generic resource set, a list subclass containing resource ranges.

  This is a virtual class.  You probably don't want to use it
  directly.
  """

  ## @var inherit
  # Boolean indicating whether this resource_set uses RFC 3779 inheritance.

  inherit = False

  ## @var canonical
  # Whether this resource_set is currently in canonical form.

  canonical = False

  def __init__(self, ini = None):
    """
    Initialize a resource_set.
    """
    list.__init__(self)
    if isinstance(ini, (int, long)):
      ini = str(ini)
    if ini is inherit_token:
      self.inherit = True
    elif isinstance(ini, str) and len(ini):
      self.extend(self.parse_str(s) for s in ini.split(","))
    elif isinstance(ini, tuple):
      self.parse_rfc3779_tuple(ini)
    elif isinstance(ini, list):
      self.extend(ini)
    else:
      assert ini is None or (isinstance(ini, str) and ini == ""), "Unexpected initializer: %s" % str(ini)
    self.canonize()

  def canonize(self):
    """
    Whack this resource_set into canonical form.
    """
    assert not self.inherit or not self
    if not self.canonical:
      self.sort()
      for i in xrange(len(self) - 2, -1, -1):
        if self[i].max + 1 == self[i+1].min:
          self[i] = type(self[i])(self[i].min, self[i+1].max)
          self.pop(i + 1)
      if __debug__:
        for i in xrange(0, len(self) - 1):
          assert self[i].max < self[i+1].min, "Resource overlap: %s %s" % (self[i], self[i+1])
      self.canonical = True

  def append(self, item):
    """
    Wrapper around list.append() (q.v.) to reset canonical flag.
    """
    list.append(self, item)
    self.canonical = False

  def extend(self, item):
    """
    Wrapper around list.extend() (q.v.) to reset canonical flag.
    """
    list.extend(self, item)
    self.canonical = False

  def __str__(self):
    """
    Convert a resource_set to string format.
    """
    if self.inherit:
      return inherit_token
    else:
      return ",".join(str(x) for x in self)

  def _comm(self, other):
    """
    Like comm(1), sort of.

    Returns a tuple of three resource sets: resources only in self,
    resources only in other, and resources in both.  Used (not very
    efficiently) as the basis for most set operations on resource
    sets.
    """

    assert not self.inherit
    assert type(self) is type(other), "Type mismatch %r %r" % (type(self), type(other))
    set1 = type(self)(self)             # clone and whack into canonical form
    set2 = type(other)(other)           # ditto
    only1, only2, both = [], [], []
    while set1 or set2:
      if set1 and (not set2 or set1[0].max < set2[0].min):
        only1.append(set1.pop(0))
      elif set2 and (not set1 or set2[0].max < set1[0].min):
        only2.append(set2.pop(0))
      elif set1[0].min < set2[0].min:
        _rsplit(set1, set2[0])
      elif set2[0].min < set1[0].min:
        _rsplit(set2, set1[0])
      elif set1[0].max < set2[0].max:
        _rsplit(set2, set1[0])
      elif set2[0].max < set1[0].max:
        _rsplit(set1, set2[0])
      else:
        assert set1[0].min == set2[0].min and set1[0].max == set2[0].max
        both.append(set1.pop(0))
        set2.pop(0)
    return type(self)(only1), type(self)(only2), type(self)(both)

  def union(self, other):
    """
    Set union for resource sets.
    """

    assert not self.inherit
    assert type(self) is type(other), "Type mismatch: %r %r" % (type(self), type(other))
    set1 = type(self)(self)             # clone and whack into canonical form
    set2 = type(other)(other)           # ditto
    result = []
    while set1 or set2:
      if set1 and (not set2 or set1[0].max < set2[0].min):
        result.append(set1.pop(0))
      elif set2 and (not set1 or set2[0].max < set1[0].min):
        result.append(set2.pop(0))
      else:
        this = set1.pop(0)
        that = set2.pop(0)
        assert type(this) is type(that)
        if this.min < that.min: min = this.min
        else:                   min = that.min
        if this.max > that.max: max = this.max
        else:                   max = that.max
        result.append(type(this)(min, max))
        while set1 and set1[0].max <= max:
          assert set1[0].min >= min
          del set1[0]
        while set2 and set2[0].max <= max:
          assert set2[0].min >= min
          del set2[0]
    return type(self)(result)

  def intersection(self, other):
    """
    Set intersection for resource sets.
    """
    return self._comm(other)[2]

  def difference(self, other):
    """
    Set difference for resource sets.
    """
    return self._comm(other)[0]

  def symmetric_difference(self, other):
    """
    Set symmetric difference (XOR) for resource sets.
    """
    com = self._comm(other)
    return com[0].union(com[1])

  def contains(self, item):
    """
    Set membership test for resource sets.
    """
    assert not self.inherit
    self.canonize()
    if not self:
      return False
    if type(item) is type(self[0]):
      min = item.min
      max = item.max
    else:
      min = item
      max = item
    lo = 0
    hi = len(self)
    while lo < hi:
      mid = (lo + hi) / 2
      if self[mid].max < max:
        lo = mid + 1
      else:
        hi = mid
    return lo < len(self) and self[lo].min <= min and self[lo].max >= max

  def issubset(self, other):
    """
    Test whether self is a subset (possibly improper) of other.
    """
    for i in self:
      if not other.contains(i):
        return False
    return True

  def issuperset(self, other):
    """
    Test whether self is a superset (possibly improper) of other.
    """
    return other.issubset(self)

  @classmethod
  def from_sql(cls, sql, query, args = None):
    """
    Create resource set from an SQL query.

    sql is an object that supports execute() and fetchall() methods
    like a DB API 2.0 cursor object.

    query is an SQL query that returns a sequence of (min, max) pairs.
    """

    sql.execute(query, args)
    return cls(ini = [cls.range_type(cls.range_type.datum_type(b),
                                     cls.range_type.datum_type(e))
                      for (b, e) in sql.fetchall()])

  @classmethod
  def parse_str(cls, s):
    """
    Parse resource set from text string (eg, XML attributes).  This is
    a backwards compatability wrapper, real functionality is now part
    of the range classes.
    """
    return cls.range_type.parse_str(s)

class resource_set_as(resource_set):
  """
  Autonomous System Number resource set.
  """

  ## @var range_type
  # Type of range underlying this type of resource_set.

  range_type = resource_range_as

  def parse_rfc3779_tuple(self, x):
    """
    Parse ASN resource from tuple format generated by RFC 3779 ASN.1
    decoder.
    """
    if x[0] == "asIdsOrRanges":
      for aor in x[1]:
        if aor[0] == "range":
          min = aor[1][0]
          max = aor[1][1]
        else:
          min = aor[1]
          max = min
        self.append(resource_range_as(min, max))
    else:
      assert x[0] == "inherit"
      self.inherit = True

  def to_rfc3779_tuple(self):
    """
    Convert ASN resource set into tuple format used for RFC 3779 ASN.1
    encoding.
    """
    self.canonize()
    if self:
      return ("asIdsOrRanges", tuple(a.to_rfc3779_tuple() for a in self))
    elif self.inherit:
      return ("inherit", "")
    else:
      return None

class resource_set_ip(resource_set):
  """
  (Generic) IP address resource set.

  This is a virtual class.  You probably don't want to use it
  directly.
  """

  def parse_rfc3779_tuple(self, x):
    """
    Parse IP address resource sets from tuple format generated by RFC
    3779 ASN.1 decoder.
    """
    if x[0] == "addressesOrRanges":
      for aor in x[1]:
        if aor[0] == "addressRange":
          min = _bs2long(aor[1][0], self.range_type.datum_type.bits, 0)
          max = _bs2long(aor[1][1], self.range_type.datum_type.bits, 1)
        else:
          min = _bs2long(aor[1], self.range_type.datum_type.bits, 0)
          max = _bs2long(aor[1], self.range_type.datum_type.bits, 1)
        self.append(self.range_type(self.range_type.datum_type(min), self.range_type.datum_type(max)))
    else:
      assert x[0] == "inherit"
      self.inherit = True

  def to_roa_prefix_set(self):
    """
    Convert from a resource set to a ROA prefix set.
    """
    prefix_ranges = []
    for r in self:
      r.chop_into_prefixes(prefix_ranges)
    return self.roa_prefix_set_type([
      self.roa_prefix_set_type.prefix_type(r.min, r.prefixlen())
      for r in prefix_ranges])

  def to_rfc3779_tuple(self):
    """
    Convert IP resource set into tuple format used by RFC 3779 ASN.1
    encoder.
    """
    self.canonize()
    if self:
      return (self.afi, ("addressesOrRanges", tuple(a.to_rfc3779_tuple() for a in self)))
    elif self.inherit:
      return (self.afi, ("inherit", ""))
    else:
      return None

class resource_set_ipv4(resource_set_ip):
  """
  IPv4 address resource set.
  """

  ## @var range_type
  # Type of range underlying this type of resource_set.

  range_type = resource_range_ipv4

  ## @var afi
  # Address Family Identifier value for IPv4.

  afi = "\x00\x01"

class resource_set_ipv6(resource_set_ip):
  """
  IPv6 address resource set.
  """

  ## @var range_type
  # Type of range underlying this type of resource_set.

  range_type = resource_range_ipv6

  ## @var afi
  # Address Family Identifier value for IPv6.

  afi = "\x00\x02"

def _bs2long(bs, addrlen, fill):
  """
  Utility function to convert a bitstring (rpki.POW.pkix tuple
  representation) into a Python long.
  """
  x = 0L
  for y in bs:
    x = (x << 1) | y
  for y in xrange(addrlen - len(bs)):
    x = (x << 1) | fill
  return x

def _long2bs(number, addrlen, prefixlen = None, strip = None):
  """
  Utility function to convert a Python long into a rpki.POW.pkix tuple
  bitstring.  This is a bit complicated because it supports the
  fiendishly compact encoding used in RFC 3779.
  """
  assert prefixlen is None or strip is None
  bs = []
  while number:
    bs.append(int(number & 1))
    number >>= 1
  if addrlen > len(bs):
    bs.extend((0 for i in xrange(addrlen - len(bs))))
  bs.reverse()
  if prefixlen is not None:
    return tuple(bs[0:prefixlen])
  if strip is not None:
    while bs and bs[-1] == strip:
      bs.pop()
  return tuple(bs)

class resource_bag(object):
  """
  Container to simplify passing around the usual triple of ASN, IPv4,
  and IPv6 resource sets.
  """

  ## @var asn
  # Set of Autonomous System Number resources.

  ## @var v4
  # Set of IPv4 resources.

  ## @var v6
  # Set of IPv6 resources.

  ## @var valid_until
  # Expiration date of resources, for setting certificate notAfter field.

  def __init__(self, asn = None, v4 = None, v6 = None, valid_until = None):
    self.asn = asn or resource_set_as()
    self.v4 = v4 or resource_set_ipv4()
    self.v6 = v6 or resource_set_ipv6()
    self.valid_until = valid_until

  def oversized(self, other):
    """
    True iff self is oversized with respect to other.
    """
    return not self.asn.issubset(other.asn) or \
           not self.v4.issubset(other.v4) or \
           not self.v6.issubset(other.v6)

  def undersized(self, other):
    """
    True iff self is undersized with respect to other.
    """
    return not other.asn.issubset(self.asn) or \
           not other.v4.issubset(self.v4) or \
           not other.v6.issubset(self.v6)

  @classmethod
  def from_inheritance(cls):
    """
    Build a resource bag that just inherits everything from its
    parent.
    """
    self = cls()
    self.asn = resource_set_as()
    self.v4 = resource_set_ipv4()
    self.v6 = resource_set_ipv6()
    self.asn.inherit = True
    self.v4.inherit = True
    self.v6.inherit = True
    return self

  @classmethod
  def from_rfc3779_tuples(cls, exts):
    """
    Build a resource_bag from intermediate form generated by RFC 3779
    ASN.1 decoder.
    """
    asn = None
    v4 = None
    v6 = None
    for x in exts:
      if x[0] == rpki.oids.name2oid["sbgp-autonomousSysNum"]:
        assert len(x[2]) == 1 or x[2][1] is None, "RDI not implemented: %s" % (str(x))
        assert asn is None
        asn = resource_set_as(x[2][0])
      if x[0] == rpki.oids.name2oid["sbgp-ipAddrBlock"]:
        for fam in x[2]:
          if fam[0] == resource_set_ipv4.afi:
            assert v4 is None
            v4 = resource_set_ipv4(fam[1])
          if fam[0] == resource_set_ipv6.afi:
            assert v6 is None
            v6 = resource_set_ipv6(fam[1])
    return cls(asn, v4, v6)

  def empty(self):
    """
    True iff all resource sets in this bag are empty.
    """
    return not self.asn and not self.v4 and not self.v6

  def __eq__(self, other):
    return self.asn == other.asn and \
           self.v4 == other.v4 and \
           self.v6 == other.v6 and \
           self.valid_until == other.valid_until

  def __ne__(self, other):
    return not (self == other)

  def intersection(self, other):
    """
    Compute intersection with another resource_bag.  valid_until
    attribute (if any) inherits from self.
    """
    return self.__class__(self.asn.intersection(other.asn),
                          self.v4.intersection(other.v4),
                          self.v6.intersection(other.v6),
                          self.valid_until)

  def union(self, other):
    """
    Compute union with another resource_bag.  valid_until attribute
    (if any) inherits from self.
    """
    return self.__class__(self.asn.union(other.asn),
                          self.v4.union(other.v4),
                          self.v6.union(other.v6),
                          self.valid_until)

  def __str__(self):
    s = ""
    if self.asn:
      s += "ASN: %s" % self.asn
    if self.v4:
      if s:
        s += ", "
      s += "V4: %s" % self.v4
    if self.v6:
      if s:
        s += ", "
      s += "V6: %s" % self.v6
    return s

# Sadly, there are enough differences between RFC 3779 and the data
# structures in the latest proposed ROA format that we can't just use
# the RFC 3779 code for ROAs.  So we need a separate set of classes
# that are similar in concept but different in detail, with conversion
# functions.  Such is life.  I suppose it might be possible to do this
# with multiple inheritance, but that's probably more bother than it's
# worth.

class roa_prefix(object):
  """
  ROA prefix.  This is similar to the resource_range_ip class, but
  differs in that it only represents prefixes, never ranges, and
  includes the maximum prefix length as an additional value.

  This is a virtual class, you probably don't want to use it directly.
  """

  ## @var prefix
  # The prefix itself, an IP address with bits beyond the prefix
  # length zeroed.

  ## @var prefixlen
  # (Minimum) prefix length.

  ## @var max_prefixlen
  # Maxmimum prefix length.

  def __init__(self, prefix, prefixlen, max_prefixlen = None):
    """
    Initialize a ROA prefix.  max_prefixlen is optional and defaults
    to prefixlen.  max_prefixlen must not be smaller than prefixlen.
    """
    if max_prefixlen is None:
      max_prefixlen = prefixlen
    assert max_prefixlen >= prefixlen, "Bad max_prefixlen: %d must not be shorter than %d" % (max_prefixlen, prefixlen)
    self.prefix = prefix
    self.prefixlen = prefixlen
    self.max_prefixlen = max_prefixlen

  def __cmp__(self, other):
    """
    Compare two ROA prefix objects.  Comparision is based on prefix,
    prefixlen, and max_prefixlen, in that order.
    """
    assert self.__class__ is other.__class__
    return (cmp(self.prefix,        other.prefix)    or
            cmp(self.prefixlen,     other.prefixlen) or
            cmp(self.max_prefixlen, other.max_prefixlen))

  def __str__(self):
    """
    Convert a ROA prefix to string format.
    """
    if self.prefixlen == self.max_prefixlen:
      return str(self.prefix) + "/" + str(self.prefixlen)
    else:
      return str(self.prefix) + "/" + str(self.prefixlen) + "-" + str(self.max_prefixlen)

  def to_resource_range(self):
    """
    Convert this ROA prefix to the equivilent resource_range_ip
    object.  This is an irreversable transformation because it loses
    the max_prefixlen attribute, nothing we can do about that.
    """
    return self.range_type.make_prefix(self.prefix, self.prefixlen)

  def min(self):
    """
    Return lowest address covered by prefix.
    """
    return self.prefix

  def max(self):
    """
    Return highest address covered by prefix.
    """
    t = self.range_type.datum_type
    return t(self.prefix | ((1 << (t.bits - self.prefixlen)) - 1))
    
  def to_roa_tuple(self):
    """
    Convert a resource_range_ip to tuple format for ROA ASN.1
    encoding.
    """
    return (_long2bs(self.prefix, self.range_type.datum_type.bits, prefixlen = self.prefixlen),
            None if self.prefixlen == self.max_prefixlen else self.max_prefixlen)

  @classmethod
  def parse_str(cls, x):
    """
    Parse ROA prefix from text (eg, an XML attribute).
    """
    r = re_prefix_with_maxlen.match(x)
    if r:
      return cls(cls.range_type.datum_type(r.group(1)), int(r.group(2)), int(r.group(3)))
    r = re_prefix.match(x)
    if r:
      return cls(cls.range_type.datum_type(r.group(1)), int(r.group(2)))
    raise rpki.exceptions.BadROAPrefix, 'Bad ROA prefix "%s"' % (x)

  @classmethod
  def from_roa_tuple(cls, o):
    """
    Convert from ROA ASN.1 tuple format.
    """
    assert isinstance(o, (list, tuple)), 'argument must be either list or tuple'
    return cls(cls.range_type.datum_type(_bs2long(o[0], cls.range_type.datum_type.bits, 0)), len(o[0]), o[1])

class roa_prefix_ipv4(roa_prefix):
  """
  IPv4 ROA prefix.
  """

  ## @var range_type
  # Type of corresponding resource_range_ip.

  range_type = resource_range_ipv4

class roa_prefix_ipv6(roa_prefix):
  """
  IPv6 ROA prefix.
  """

  ## @var range_type
  # Type of corresponding resource_range_ip.

  range_type = resource_range_ipv6

class roa_prefix_set(list):
  """
  Set of ROA prefixes, analogous to the resource_set_ip class.
  """

  def __init__(self, ini = None):
    """
    Initialize a ROA prefix set.
    """
    list.__init__(self)
    if isinstance(ini, str) and len(ini):
      self.extend(self.parse_str(s) for s in ini.split(","))
    elif isinstance(ini, (list, tuple)):
      self.extend(ini)
    else:
      assert ini is None or ini == "", "Unexpected initializer: %s" % str(ini)
    self.sort()

  def __str__(self):
    """
    Convert a ROA prefix set to string format.
    """
    return ",".join(str(x) for x in self)

  @classmethod
  def parse_str(cls, s):
    """
    Parse ROA prefix from text (eg, an XML attribute).
    This method is a backwards compatability shim.
    """
    return cls.prefix_type.parse_str(s)

  def to_resource_set(self):
    """
    Convert a ROA prefix set to a resource set.  This is an
    irreversable transformation.  We have to compute a union here
    because ROA prefix sets can include overlaps, while RFC 3779
    resource sets cannot.  This is ugly, and there is almost certainly
    a more efficient way to do this, but start by getting the output
    right before worrying about making it fast or pretty.
    """
    r = self.resource_set_type()
    s = self.resource_set_type()
    s.append(None)
    for p in self:
      s[0] = p.to_resource_range()
      r = r.union(s)
    return r

  @classmethod
  def from_sql(cls, sql, query, args = None):
    """
    Create ROA prefix set from an SQL query.

    sql is an object that supports execute() and fetchall() methods
    like a DB API 2.0 cursor object.

    query is an SQL query that returns a sequence of (prefix,
    prefixlen, max_prefixlen) triples.
    """

    sql.execute(query, args)
    return cls([cls.prefix_type(cls.prefix_type.range_type.datum_type(x), int(y), int(z))
                for (x, y, z) in sql.fetchall()])

  def to_roa_tuple(self):
    """
    Convert ROA prefix set into tuple format used by ROA ASN.1
    encoder.  This is a variation on the format used in RFC 3779.
    """
    if self:
      return (self.resource_set_type.afi, tuple(a.to_roa_tuple() for a in self))
    else:
      return None

class roa_prefix_set_ipv4(roa_prefix_set):
  """
  Set of IPv4 ROA prefixes.
  """

  ## @var prefix_type
  # Type of underlying roa_prefix.

  prefix_type = roa_prefix_ipv4

  ## @var resource_set_type
  # Type of corresponding resource_set_ip class.

  resource_set_type = resource_set_ipv4

# Fix back link from resource_set to roa_prefix
resource_set_ipv4.roa_prefix_set_type = roa_prefix_set_ipv4

class roa_prefix_set_ipv6(roa_prefix_set):
  """
  Set of IPv6 ROA prefixes.
  """

  ## @var prefix_type
  # Type of underlying roa_prefix.

  prefix_type = roa_prefix_ipv6

  ## @var resource_set_type
  # Type of corresponding resource_set_ip class.

  resource_set_type = resource_set_ipv6

# Fix back link from resource_set to roa_prefix
resource_set_ipv6.roa_prefix_set_type = roa_prefix_set_ipv6

# Test suite for set operations.

if __name__ == "__main__":

  def testprefix(v):
    return " (%s)" % v.to_roa_prefix_set() if isinstance(v, resource_set_ip) else ""

  def test1(t, s1, s2):
    if isinstance(s1, str) and isinstance(s2, str):
      print "x:  ", s1
      print "y:  ", s2
    r1 = t(s1)
    r2 = t(s2)
    print "x:  ", r1, testprefix(r1)
    print "y:  ", r2, testprefix(r2)
    v1 = r1._comm(r2)
    v2 = r2._comm(r1)
    assert v1[0] == v2[1] and v1[1] == v2[0] and v1[2] == v2[2]
    for i in r1: assert r1.contains(i) and r1.contains(i.min) and r1.contains(i.max)
    for i in r2: assert r2.contains(i) and r2.contains(i.min) and r2.contains(i.max)
    for i in v1[0]: assert r1.contains(i) and not r2.contains(i)
    for i in v1[1]: assert not r1.contains(i) and r2.contains(i)
    for i in v1[2]: assert r1.contains(i) and r2.contains(i)
    v1 = r1.union(r2)
    v2 = r2.union(r1)
    assert v1 == v2
    print "x|y:", v1, testprefix(v1)
    v1 = r1.difference(r2)
    v2 = r2.difference(r1)
    print "x-y:", v1, testprefix(v1)
    print "y-x:", v2, testprefix(v2)
    v1 = r1.symmetric_difference(r2)
    v2 = r2.symmetric_difference(r1)
    assert v1 == v2
    print "x^y:", v1, testprefix(v1)
    v1 = r1.intersection(r2)
    v2 = r2.intersection(r1)
    assert v1 == v2
    print "x&y:", v1, testprefix(v1)

  def test2(t, s1, s2):
    print "x:  ", s1
    print "y:  ", s2
    r1 = t(s1)
    r2 = t(s2)
    print "x:  ", r1
    print "y:  ", r2
    print "x>y:", (r1 > r2)
    print "x<y:", (r1 < r2)
    test1(t.resource_set_type,
          r1.to_resource_set(),
          r2.to_resource_set())

  def test3(t, s1, s2):
    test1(t, s1, s2)
    r1 = t(s1).to_roa_prefix_set()
    r2 = t(s2).to_roa_prefix_set()
    print "x:  ", r1
    print "y:  ", r2
    print "x>y:", (r1 > r2)
    print "x<y:", (r1 < r2)
    test1(t.roa_prefix_set_type.resource_set_type,
          r1.to_resource_set(),
          r2.to_resource_set())

  print
  print "Testing set operations on resource sets"
  print
  test1(resource_set_as, "1,2,3,4,5,6,11,12,13,14,15", "1,2,3,4,5,6,111,121,131,141,151")
  print
  test1(resource_set_ipv4, "10.0.0.44/32,10.6.0.2/32", "10.3.0.0/24,10.0.0.77/32")
  print
  test1(resource_set_ipv4, "10.0.0.44/32,10.6.0.2/32", "10.0.0.0/24")
  print
  test1(resource_set_ipv4, "10.0.0.0/24", "10.3.0.0/24,10.0.0.77/32")
  print
  test1(resource_set_ipv4, "10.0.0.0/24", "10.0.0.0/32,10.0.0.2/32,10.0.0.4/32")
  print
  print "Testing set operations on ROA prefixes"
  print
  test2(roa_prefix_set_ipv4, "10.0.0.44/32,10.6.0.2/32", "10.3.0.0/24,10.0.0.77/32")
  print
  test2(roa_prefix_set_ipv4, "10.0.0.0/24-32,10.6.0.0/24-32", "10.3.0.0/24,10.0.0.0/16-32")
  print
  test2(roa_prefix_set_ipv4, "10.3.0.0/24-24,10.0.0.0/16-32", "10.3.0.0/24,10.0.0.0/16-32")
  print
  test2(roa_prefix_set_ipv6, "2002:0a00:002c::1/128", "2002:0a00:002c::2/128")
  print
  test2(roa_prefix_set_ipv6, "2002:0a00:002c::1/128", "2002:0a00:002c::7/128")
  print
  test2(roa_prefix_set_ipv6, "2002:0a00:002c::1/128", "2002:0a00:002c::/120")
  print
  test2(roa_prefix_set_ipv6, "2002:0a00:002c::1/128", "2002:0a00:002c::/120-128")
  print
  test3(resource_set_ipv4, "10.0.0.44/32,10.6.0.2/32", "10.3.0.0/24,10.0.0.77/32")
  print
  test3(resource_set_ipv6, "2002:0a00:002c::1/128", "2002:0a00:002c::2/128")
  print
  test3(resource_set_ipv6, "2002:0a00:002c::1/128", "2002:0a00:002c::/120")
