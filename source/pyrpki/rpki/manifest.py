"""
Signed manifests.  This is just the ASN.1 encoder, the rest is in
rpki.x509 with the rest of the DER_object code.

Note that rpki.x509.SignedManifest implements the signed manifest;
the structures here are just the payload of the CMS eContent field.

$Id: manifest.py 3598 2011-01-04 05:12:16Z sra $

Copyright (C) 2007--2008  American Registry for Internet Numbers ("ARIN")

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

from rpki.POW._der import *

class FileAndHash(Sequence):
  def __init__(self, optional=0, default=''):
    self.file = IA5String()
    self.hash = AltBitString()
    contents = [ self.file, self.hash ]
    Sequence.__init__(self, contents, optional, default)

class FilesAndHashes(SequenceOf):
  def __init__(self, optional=0, default=''):
    SequenceOf.__init__(self, FileAndHash, optional, default)

class Manifest(Sequence):
  def __init__(self, optional=0, default=''):
    self.version        = Integer()      
    self.explicitVersion = Explicit(CLASS_CONTEXT, FORM_CONSTRUCTED, 0, self.version, 0, 'oAMCAQA=')
    self.manifestNumber = Integer()
    self.thisUpdate     = GeneralizedTime()
    self.nextUpdate     = GeneralizedTime()
    self.fileHashAlg    = Oid()
    self.fileList       = FilesAndHashes()

    contents = [ self.explicitVersion,
                 self.manifestNumber,
                 self.thisUpdate,
                 self.nextUpdate,
                 self.fileHashAlg,
                 self.fileList ]
    Sequence.__init__(self, contents, optional, default)
