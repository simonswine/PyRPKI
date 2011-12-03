"""
XML utilities.

$Id: xml_utils.py 3725 2011-03-18 03:51:12Z sra $

Copyright (C) 2009-2011  Internet Systems Consortium ("ISC")

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

import xml.sax, lxml.sax, lxml.etree
import rpki.exceptions

class sax_handler(xml.sax.handler.ContentHandler):
  """
  SAX handler for RPKI protocols.

  This class provides some basic amenities for parsing protocol XML of
  the kind we use in the RPKI protocols, including whacking all the
  protocol element text into US-ASCII, simplifying accumulation of
  text fields, and hiding some of the fun relating to XML namespaces.

  General assumption: by the time this parsing code gets invoked, the
  XML has already passed RelaxNG validation, so we only have to check
  for errors that the schema can't catch, and we don't have to play as
  many XML namespace games.
  """

  def __init__(self):
    """
    Initialize SAX handler.
    """
    xml.sax.handler.ContentHandler.__init__(self)
    self.text = ""
    self.stack = []

  def startElementNS(self, name, qname, attrs):
    """
    Redirect startElementNS() events to startElement().
    """
    return self.startElement(name[1], attrs)

  def endElementNS(self, name, qname):
    """
    Redirect endElementNS() events to endElement().
    """
    return self.endElement(name[1])

  def characters(self, content):
    """
    Accumulate a chuck of element content (text).
    """
    self.text += content

  def startElement(self, name, attrs):
    """
    Handle startElement() events.

    We maintain a stack of nested elements under construction so that
    we can feed events directly to the current element rather than
    having to pass them through all the nesting elements.

    If the stack is empty, this event is for the outermost element, so
    we call a virtual method to create the corresponding object and
    that's the object we'll be returning as our final result.
    """

    a = dict()
    for k, v in attrs.items():
      if isinstance(k, tuple):
        if k == ("http://www.w3.org/XML/1998/namespace", "lang"):
          k = "xml:lang"
        else:
          assert k[0] is None
          k = k[1]
      a[k.encode("ascii")] = v.encode("ascii")
    if len(self.stack) == 0:
      assert not hasattr(self, "result")
      self.result = self.create_top_level(name, a)
      self.stack.append(self.result)
    self.stack[-1].startElement(self.stack, name, a)

  def endElement(self, name):
    """
    Handle endElement() events.  Mostly this means handling any
    accumulated element text.
    """
    text = self.text.encode("ascii").strip()
    self.text = ""
    self.stack[-1].endElement(self.stack, name, text)

  @classmethod
  def saxify(cls, elt):
    """
    Create a one-off SAX parser, parse an ETree, return the result.
    """
    self = cls()
    lxml.sax.saxify(elt, self)
    return self.result

  def create_top_level(self, name, attrs):
    """
    Handle top-level PDU for this protocol.
    """
    assert name == self.name and attrs["version"] == self.version
    return self.pdu()

class base_elt(object):
  """
  Virtual base class for XML message elements.  The left-right and
  publication protocols use this.  At least for now, the up-down
  protocol does not, due to different design assumptions.
  """

  ## @var attributes
  # XML attributes for this element.
  attributes = ()

  ## @var elements
  # XML elements contained by this element.
  elements = ()

  ## @var booleans
  # Boolean attributes (value "yes" or "no") for this element.
  booleans = ()

  def startElement(self, stack, name, attrs):
    """
    Default startElement() handler: just process attributes.
    """
    if name not in self.elements:
      assert name == self.element_name, "Unexpected name %s, stack %s" % (name, stack)
      self.read_attrs(attrs)

  def endElement(self, stack, name, text):
    """
    Default endElement() handler: just pop the stack.
    """
    assert name == self.element_name, "Unexpected name %s, stack %s" % (name, stack)
    stack.pop()

  def toXML(self):
    """
    Default toXML() element generator.
    """
    return self.make_elt()

  def read_attrs(self, attrs):
    """
    Template-driven attribute reader.
    """
    for key in self.attributes:
      val = attrs.get(key, None)
      if isinstance(val, str) and val.isdigit() and not key.endswith("_handle"):
        val = long(val)
      setattr(self, key, val)
    for key in self.booleans:
      setattr(self, key, attrs.get(key, False))

  def make_elt(self):
    """
    XML element constructor.
    """
    elt = lxml.etree.Element("{%s}%s" % (self.xmlns, self.element_name), nsmap = self.nsmap)
    for key in self.attributes:
      val = getattr(self, key, None)
      if val is not None:
        elt.set(key, str(val))
    for key in self.booleans:
      if getattr(self, key, False):
        elt.set(key, "yes")
    return elt

  def make_b64elt(self, elt, name, value):
    """
    Constructor for Base64-encoded subelement.
    """
    if value is not None and not value.empty():
      lxml.etree.SubElement(elt, "{%s}%s" % (self.xmlns, name), nsmap = self.nsmap).text = value.get_Base64()

  def __str__(self):
    """
    Convert a base_elt object to string format.
    """
    lxml.etree.tostring(self.toXML(), pretty_print = True, encoding = "us-ascii")

  @classmethod
  def make_pdu(cls, **kargs):
    """
    Generic PDU constructor.
    """
    self = cls()
    for k, v in kargs.items():
      if isinstance(v, bool):
        v = 1 if v else 0
      setattr(self, k, v)
    return self

class text_elt(base_elt):
  """
  Virtual base class for XML message elements that contain text.
  """

  ## @var text_attribute
  # Name of the class attribute that holds the text value.
  text_attribute = None

  def endElement(self, stack, name, text):
    """
    Extract text from parsed XML.
    """
    base_elt.endElement(self, stack, name, text)
    setattr(self, self.text_attribute, text)

  def toXML(self):
    """
    Insert text into generated XML.
    """
    elt = self.make_elt()
    elt.text = getattr(self, self.text_attribute) or None
    return elt

class data_elt(base_elt):
  """
  Virtual base class for PDUs that map to SQL objects.  These objects
  all implement the create/set/get/list/destroy action attribute.
  """

  def endElement(self, stack, name, text):
    """
    Default endElement handler for SQL-based objects.  This assumes
    that sub-elements are Base64-encoded using the sql_template
    mechanism.
    """
    if name in self.elements:
      elt_type = self.sql_template.map.get(name)
      assert elt_type is not None, "Couldn't find element type for %s, stack %s" % (name, stack)
      setattr(self, name, elt_type(Base64 = text))
    else:
      assert name == self.element_name, "Unexpected name %s, stack %s" % (name, stack)
      stack.pop()

  def toXML(self):
    """
    Default element generator for SQL-based objects.  This assumes
    that sub-elements are Base64-encoded DER objects.
    """
    elt = self.make_elt()
    for i in self.elements:
      self.make_b64elt(elt, i, getattr(self, i, None))
    return elt

  def make_reply(self, r_pdu = None):
    """
    Construct a reply PDU.
    """
    if r_pdu is None:
      r_pdu = self.__class__()
      self.make_reply_clone_hook(r_pdu)
      handle_name = self.element_name + "_handle"
      setattr(r_pdu, handle_name, getattr(self, handle_name, None))
    else:
      self.make_reply_clone_hook(r_pdu)
      for b in r_pdu.booleans:
        setattr(r_pdu, b, False)
    r_pdu.action = self.action
    r_pdu.tag = self.tag
    return r_pdu

  def make_reply_clone_hook(self, r_pdu):
    """
    Overridable hook.
    """
    pass

  def serve_fetch_one(self):
    """
    Find the object on which a get, set, or destroy method should
    operate.
    """
    r = self.serve_fetch_one_maybe()
    if r is None:
      raise rpki.exceptions.NotFound
    return r

  def serve_pre_save_hook(self, q_pdu, r_pdu, cb, eb):
    """
    Overridable hook.
    """
    cb()

  def serve_post_save_hook(self, q_pdu, r_pdu, cb, eb):
    """
    Overridable hook.
    """
    cb()

  def serve_create(self, r_msg, cb, eb):
    """
    Handle a create action.
    """

    r_pdu = self.make_reply()

    def one():
      self.sql_store()
      setattr(r_pdu, self.sql_template.index, getattr(self, self.sql_template.index))
      self.serve_post_save_hook(self, r_pdu, two, eb)

    def two():
      r_msg.append(r_pdu)
      cb()

    oops = self.serve_fetch_one_maybe()
    if oops is not None:
      raise rpki.exceptions.DuplicateObject, "Object already exists: %r[%r] %r[%r]" % (self, getattr(self, self.element_name + "_handle"),
                                                                                       oops, getattr(oops, oops.element_name + "_handle"))

    self.serve_pre_save_hook(self, r_pdu, one, eb)

  def serve_set(self, r_msg, cb, eb):
    """
    Handle a set action.
    """

    db_pdu = self.serve_fetch_one()
    r_pdu = self.make_reply()
    for a in db_pdu.sql_template.columns[1:]:
      v = getattr(self, a, None)
      if v is not None:
        setattr(db_pdu, a, v)
    db_pdu.sql_mark_dirty()

    def one():
      db_pdu.sql_store()
      db_pdu.serve_post_save_hook(self, r_pdu, two, eb)

    def two():
      r_msg.append(r_pdu)
      cb()

    db_pdu.serve_pre_save_hook(self, r_pdu, one, eb)

  def serve_get(self, r_msg, cb, eb):
    """
    Handle a get action.
    """
    r_pdu = self.serve_fetch_one()
    self.make_reply(r_pdu)
    r_msg.append(r_pdu)
    cb()

  def serve_list(self, r_msg, cb, eb):
    """
    Handle a list action for non-self objects.
    """
    for r_pdu in self.serve_fetch_all():
      self.make_reply(r_pdu)
      r_msg.append(r_pdu)
    cb()

  def serve_destroy_hook(self, cb, eb):
    """
    Overridable hook.
    """
    cb()

  def serve_destroy(self, r_msg, cb, eb):
    """
    Handle a destroy action.
    """
    def done():
      db_pdu.sql_delete()
      r_msg.append(self.make_reply())
      cb()
    db_pdu = self.serve_fetch_one()
    db_pdu.serve_destroy_hook(done, eb)

  def serve_dispatch(self, r_msg, cb, eb):
    """
    Action dispatch handler.
    """
    dispatch = { "create"  : self.serve_create,
                 "set"     : self.serve_set,
                 "get"     : self.serve_get,
                 "list"    : self.serve_list,
                 "destroy" : self.serve_destroy }
    if self.action not in dispatch:
      raise rpki.exceptions.BadQuery, "Unexpected query: action %s" % self.action
    dispatch[self.action](r_msg, cb, eb)
  
  def unimplemented_control(self, *controls):
    """
    Uniform handling for unimplemented control operations.
    """
    unimplemented = [x for x in controls if getattr(self, x, False)]
    if unimplemented:
      raise rpki.exceptions.NotImplementedYet, "Unimplemented control %s" % ", ".join(unimplemented)

class msg(list):
  """
  Generic top-level PDU.
  """

  def startElement(self, stack, name, attrs):
    """
    Handle top-level PDU.
    """
    if name == "msg":
      assert self.version == int(attrs["version"])
      self.type = attrs["type"]
    else:
      elt = self.pdus[name]()
      self.append(elt)
      stack.append(elt)
      elt.startElement(stack, name, attrs)

  def endElement(self, stack, name, text):
    """
    Handle top-level PDU.
    """
    assert name == "msg", "Unexpected name %s, stack %s" % (name, stack)
    assert len(stack) == 1
    stack.pop()

  def __str__(self):
    """
    Convert msg object to string.
    """
    lxml.etree.tostring(self.toXML(), pretty_print = True, encoding = "us-ascii")

  def toXML(self):
    """
    Generate top-level PDU.
    """
    elt = lxml.etree.Element("{%s}msg" % (self.xmlns), nsmap = self.nsmap, version = str(self.version), type = self.type)
    elt.extend([i.toXML() for i in self])
    return elt

  @classmethod
  def query(cls, *args):
    """
    Create a query PDU.
    """
    self = cls(args)
    self.type = "query"
    return self

  @classmethod
  def reply(cls, *args):
    """
    Create a reply PDU.
    """
    self = cls(args)
    self.type = "reply"
    return self

  def is_query(self):
    """
    Is this msg a query?
    """
    return self.type == "query"

  def is_reply(self):
    """
    Is this msg a reply?
    """
    return self.type == "reply"
