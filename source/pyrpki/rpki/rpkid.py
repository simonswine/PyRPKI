"""
RPKI engine daemon.

Usage: python rpkid.py [ { -c | --config } configfile ]
                       [ { -h | --help } ]
                       [ { -p | --profile } outputfile ]

$Id: rpkid.py 4014 2011-10-05 16:30:24Z sra $

Copyright (C) 2009--2011  Internet Systems Consortium ("ISC")

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

import os, time, getopt, sys, lxml.etree, re, random
import rpki.resource_set, rpki.up_down, rpki.left_right, rpki.x509, rpki.sql
import rpki.http, rpki.config, rpki.exceptions, rpki.relaxng, rpki.log, rpki.async

class main(object):
  """
  Main program for rpkid.
  """

  def __init__(self):

    os.environ["TZ"] = "UTC"
    time.tzset()

    self.cfg_file = None
    self.profile = None

    opts, argv = getopt.getopt(sys.argv[1:], "c:dhp:?", ["config=", "debug", "help", "profile="])
    for o, a in opts:
      if o in ("-h", "--help", "-?"):
        print __doc__
        sys.exit(0)
      elif o in ("-d", "--debug"):
        rpki.log.use_syslog = False
      elif o in ("-c", "--config"):
        self.cfg_file = a
      elif o in ("-p", "--profile"):
        self.profile = a
    if argv:
      raise rpki.exceptions.CommandParseFailure, "Unexpected arguments %s" % argv

    rpki.log.init("rpkid")

    if self.profile:
      import cProfile
      cProfile.run("self.main()", self.profile)
    else:
      self.main()

  def main(self):

    self.cfg = rpki.config.parser(self.cfg_file, "rpkid")

    startup_msg = self.cfg.get("startup-message", "")
    if startup_msg:
      rpki.log.info(startup_msg)

    if self.profile:
      rpki.log.info("Running in profile mode with output to %s" % self.profile)

    self.cfg.set_global_flags()

    self.sql = rpki.sql.session(self.cfg)

    self.bpki_ta    = rpki.x509.X509(Auto_update = self.cfg.get("bpki-ta"))
    self.irdb_cert  = rpki.x509.X509(Auto_update = self.cfg.get("irdb-cert"))
    self.irbe_cert  = rpki.x509.X509(Auto_update = self.cfg.get("irbe-cert"))
    self.rpkid_cert = rpki.x509.X509(Auto_update = self.cfg.get("rpkid-cert"))
    self.rpkid_key  = rpki.x509.RSA( Auto_update = self.cfg.get("rpkid-key"))

    self.irdb_url   = self.cfg.get("irdb-url")

    self.http_server_host = self.cfg.get("server-host", "")
    self.http_server_port = self.cfg.getint("server-port", 4433)

    self.publication_kludge_base = self.cfg.get("publication-kludge-base", "publication/")

    self.use_internal_cron = self.cfg.getboolean("use-internal-cron", True)

    self.initial_delay = random.randint(self.cfg.getint("initial-delay-min", 10),
                                        self.cfg.getint("initial-delay-max", 120))
    
    # Should be much longer in production
    self.cron_period = rpki.sundial.timedelta(seconds = self.cfg.getint("cron-period", 120))
    self.cron_keepalive = rpki.sundial.timedelta(seconds = self.cfg.getint("cron-keepalive", 0))
    if not self.cron_keepalive:
      self.cron_keepalive = self.cron_period * 4
    self.cron_timeout = None

    self.start_cron()

    rpki.http.server(
      host     = self.http_server_host,
      port     = self.http_server_port,
      handlers = (("/left-right", self.left_right_handler),
                  ("/up-down/",   self.up_down_handler),
                  ("/cronjob",    self.cronjob_handler)))


  def start_cron(self):
    """
    Start clock for rpkid's internal cron process.
    """

    if self.use_internal_cron:
      self.cron_timer = rpki.async.timer(handler = self.cron)
      when = rpki.sundial.now() + rpki.sundial.timedelta(seconds = self.initial_delay)
      rpki.log.debug("Scheduling initial cron pass at %s" % when)
      self.cron_timer.set(when)
    else:
      rpki.log.debug("Not using internal clock, start_cron() call ignored")

  def irdb_query(self, callback, errback, *q_pdus, **kwargs):
    """
    Perform an IRDB callback query.
    """

    rpki.log.trace()

    q_types = tuple(type(q_pdu) for q_pdu in q_pdus)

    expected_pdu_count = kwargs.pop("expected_pdu_count", None)
    assert len(kwargs) == 0

    q_msg = rpki.left_right.msg.query()
    q_msg.extend(q_pdus)
    q_der = rpki.left_right.cms_msg().wrap(q_msg, self.rpkid_key, self.rpkid_cert)

    def unwrap(r_der):
      r_cms = rpki.left_right.cms_msg(DER = r_der)
      r_msg = r_cms.unwrap((self.bpki_ta, self.irdb_cert))
      if not r_msg.is_reply() or not all(type(r_pdu) in q_types for r_pdu in r_msg):
        raise rpki.exceptions.BadIRDBReply, "Unexpected response to IRDB query: %s" % r_cms.pretty_print_content()
      if expected_pdu_count is not None and len(r_msg) != expected_pdu_count:
        assert isinstance(expected_pdu_count, (int, long))
        raise rpki.exceptions.BadIRDBReply, "Expected exactly %d PDU%s from IRDB: %s" % (
          expected_pdu_count, "" if expected_pdu_count == 1 else "s", r_cms.pretty_print_content())
      callback(r_msg)

    rpki.http.client(
      url          = self.irdb_url,
      msg          = q_der,
      callback     = unwrap,
      errback      = errback)

  def irdb_query_child_resources(self, self_handle, child_handle, callback, errback):
    """
    Ask IRDB about a child's resources.
    """

    rpki.log.trace()

    q_pdu = rpki.left_right.list_resources_elt()
    q_pdu.self_handle = self_handle
    q_pdu.child_handle = child_handle

    def done(r_msg):
      callback(rpki.resource_set.resource_bag(
        asn         = r_msg[0].asn,
        v4          = r_msg[0].ipv4,
        v6          = r_msg[0].ipv6,
        valid_until = r_msg[0].valid_until))

    self.irdb_query(done, errback, q_pdu, expected_pdu_count = 1)

  def irdb_query_roa_requests(self, self_handle, callback, errback):
    """
    Ask IRDB about self's ROA requests.
    """

    rpki.log.trace()

    q_pdu = rpki.left_right.list_roa_requests_elt()
    q_pdu.self_handle = self_handle

    self.irdb_query(callback, errback, q_pdu)

  def irdb_query_ghostbuster_requests(self, self_handle, parent_handles, callback, errback):
    """
    Ask IRDB about self's ghostbuster record requests.
    """

    rpki.log.trace()

    q_pdus = []

    for parent_handle in parent_handles:
      q_pdu = rpki.left_right.list_ghostbuster_requests_elt()
      q_pdu.self_handle = self_handle
      q_pdu.parent_handle = parent_handle
      q_pdus.append(q_pdu)

    self.irdb_query(callback, errback, *q_pdus)

  def left_right_handler(self, query, path, cb):
    """
    Process one left-right PDU.
    """

    rpki.log.trace()

    def done(r_msg):
      reply = rpki.left_right.cms_msg().wrap(r_msg, self.rpkid_key, self.rpkid_cert)
      self.sql.sweep()
      cb(200, body = reply)

    try:
      self.sql.ping()
      q_msg = rpki.left_right.cms_msg(DER = query).unwrap((self.bpki_ta, self.irbe_cert))
      if not q_msg.is_query():
        raise rpki.exceptions.BadQuery, "Message type is not query"
      q_msg.serve_top_level(self, done)
    except (rpki.async.ExitNow, SystemExit):
      raise
    except Exception, e:
      rpki.log.traceback()
      cb(500, reason = "Unhandled exception %s" % e)

  up_down_url_regexp = re.compile("/up-down/([-A-Z0-9_]+)/([-A-Z0-9_]+)$", re.I)

  def up_down_handler(self, query, path, cb):
    """
    Process one up-down PDU.
    """

    rpki.log.trace()

    def done(reply):
      self.sql.sweep()
      cb(200, body = reply)

    try:
      self.sql.ping()
      match = self.up_down_url_regexp.search(path)
      if match is None:
        raise rpki.exceptions.BadContactURL, "Bad URL path received in up_down_handler(): %s" % path
      self_handle, child_handle = match.groups()
      child = rpki.left_right.child_elt.sql_fetch_where1(self, "self.self_handle = %s AND child.child_handle = %s AND child.self_id = self.self_id",
                                                         (self_handle, child_handle), "self")
      if child is None:
        raise rpki.exceptions.ChildNotFound, "Could not find child %s of self %s in up_down_handler()" % (child_handle, self_handle)
      child.serve_up_down(query, done)
    except (rpki.async.ExitNow, SystemExit):
      raise
    except (rpki.exceptions.ChildNotFound, rpki.exceptions.BadContactURL), e:
      rpki.log.warn(str(e))
      cb(400, reason = str(e))
    except Exception, e:
      rpki.log.traceback()
      cb(400, reason = "Could not process PDU: %s" % e)

  def checkpoint(self, force = False):
    """
    Record that we were still alive when we got here, by resetting
    keepalive timer.
    """
    if force or self.cron_timeout is not None:
      self.cron_timeout = rpki.sundial.now() + self.cron_keepalive

  def cron(self, cb = None):
    """
    Periodic tasks.
    """

    rpki.log.trace()

    def loop(iterator, s):
      self.checkpoint()
      s.cron(iterator)

    def done():
      self.sql.sweep()
      self.cron_timeout = None
      rpki.log.info("Finished cron run started at %s" % now)
      if not self.use_internal_cron:
        cb()

    def lose(e):
      self.cron_timeout = None
      if self.use_internal_cron:
        rpki.log.traceback()
      else:
        raise
      
    try:
      now = rpki.sundial.now()

      assert self.use_internal_cron or self.cron_timeout is None

      if self.use_internal_cron:

        if self.cron_timeout is not None and self.cron_timeout < now:
          rpki.log.warn("cron keepalive threshold %s has expired, breaking lock" % self.cron_timeout)
          self.cron_timeout = None

        when = now + self.cron_period
        rpki.log.debug("Scheduling next cron run at %s" % when)
        self.cron_timer.set(when)

        if self.cron_timeout is not None:
          rpki.log.warn("cron already running, keepalive will expire at %s" % self.cron_timeout)
          return

      self.sql.ping()
      self.checkpoint(self.use_internal_cron)
      rpki.async.iterator(rpki.left_right.self_elt.sql_fetch_all(self), loop, done)

    except (rpki.async.ExitNow, SystemExit):
      self.cron_timeout = None
      raise

    except Exception, e:
      lose(e)

  def cronjob_handler(self, query, path, cb):
    """
    External trigger for periodic tasks.  This is somewhat obsolete
    now that we have internal timers, but the test framework still
    uses it.
    """

    def done():
      cb(200, body = "OK")

    if self.use_internal_cron:
      cb(500, reason = "Running cron internally")
    else:
      self.cron(done)

class ca_obj(rpki.sql.sql_persistent):
  """
  Internal CA object.
  """

  sql_template = rpki.sql.template(
    "ca",
    "ca_id",
    "last_crl_sn",
    ("next_crl_update", rpki.sundial.datetime),
    "last_issued_sn", "last_manifest_sn",
    ("next_manifest_update", rpki.sundial.datetime),
    "sia_uri", "parent_id", "parent_resource_class")

  last_crl_sn = 0
  last_issued_sn = 0
  last_manifest_sn = 0

  @property
  def parent(self):
    """
    Fetch parent object to which this CA object links.
    """
    return rpki.left_right.parent_elt.sql_fetch(self.gctx, self.parent_id)

  @property
  def ca_details(self):
    """
    Fetch all ca_detail objects that link to this CA object.
    """
    return ca_detail_obj.sql_fetch_where(self.gctx, "ca_id = %s", (self.ca_id,))

  @property
  def pending_ca_details(self):
    """
    Fetch the pending ca_details for this CA, if any.
    """
    return ca_detail_obj.sql_fetch_where(self.gctx, "ca_id = %s AND state = 'pending'", (self.ca_id,))

  @property
  def active_ca_detail(self):
    """
    Fetch the active ca_detail for this CA, if any.
    """
    return ca_detail_obj.sql_fetch_where1(self.gctx, "ca_id = %s AND state = 'active'", (self.ca_id,))

  @property
  def deprecated_ca_details(self):
    """
    Fetch deprecated ca_details for this CA, if any.
    """
    return ca_detail_obj.sql_fetch_where(self.gctx, "ca_id = %s AND state = 'deprecated'", (self.ca_id,))

  @property
  def revoked_ca_details(self):
    """
    Fetch revoked ca_details for this CA, if any.
    """
    return ca_detail_obj.sql_fetch_where(self.gctx, "ca_id = %s AND state = 'revoked'", (self.ca_id,))

  @property
  def issue_response_candidate_ca_details(self):
    """
    Fetch ca_details which are candidates for consideration when
    processing an up-down issue_response PDU.
    """
    #return ca_detail_obj.sql_fetch_where(self.gctx, "ca_id = %s AND latest_ca_cert IS NOT NULL AND state != 'revoked'", (self.ca_id,))
    return ca_detail_obj.sql_fetch_where(self.gctx, "ca_id = %s AND state != 'revoked'", (self.ca_id,))

  def construct_sia_uri(self, parent, rc):
    """
    Construct the sia_uri value for this CA given configured
    information and the parent's up-down protocol list_response PDU.
    """

    sia_uri = rc.suggested_sia_head and rc.suggested_sia_head.rsync()
    if not sia_uri or not sia_uri.startswith(parent.sia_base):
      sia_uri = parent.sia_base
    if not sia_uri.endswith("/"):
      raise rpki.exceptions.BadURISyntax, "SIA URI must end with a slash: %s" % sia_uri
    return sia_uri + str(self.ca_id) + "/"

  def check_for_updates(self, parent, rc, cb, eb):
    """
    Parent has signaled continued existance of a resource class we
    already knew about, so we need to check for an updated
    certificate, changes in resource coverage, revocation and reissue
    with the same key, etc.
    """

    sia_uri = self.construct_sia_uri(parent, rc)
    sia_uri_changed = self.sia_uri != sia_uri
    if sia_uri_changed:
      self.sia_uri = sia_uri
      self.sql_mark_dirty()

    rc_resources = rc.to_resource_bag()
    cert_map = dict((c.cert.get_SKI(), c) for c in rc.certs)

    def loop(iterator, ca_detail):

      self.gctx.checkpoint()

      rc_cert = cert_map.pop(ca_detail.public_key.get_SKI(), None)

      if rc_cert is None:

        rpki.log.warn("SKI %s in resource class %s is in my database but missing from list_response received from %s, maybe parent certificate went away?"
                      % (ca_detail.public_key.gSKI(), rc.class_name, parent.parent_handle))
        publisher = publication_queue()
        ca_detail.delete(ca = ca_detail.ca, publisher = publisher)
        return publisher.call_pubd(iterator, eb)

      else:

        if ca_detail.state in ("pending", "active"):

          if ca_detail.state == "pending":
            current_resources = rpki.resource_set.resource_bag()
          else:
            current_resources = ca_detail.latest_ca_cert.get_3779resources()

          if (ca_detail.state == "pending" or
              sia_uri_changed or
              ca_detail.latest_ca_cert != rc_cert.cert or
              current_resources.undersized(rc_resources) or
              current_resources.oversized(rc_resources)):
            return ca_detail.update(
              parent           = parent,
              ca               = self,
              rc               = rc,
              sia_uri_changed  = sia_uri_changed,
              old_resources    = current_resources,
              callback         = iterator,
              errback          = eb)

      iterator()

    def done():
      if cert_map:
        rpki.log.warn("Certificate SKIs in resource class %s in list_response from parent %s that are missing from our database: %s"
                      % (rc.class_name, parent.parent_handle, ", ".join(c.cert.gSKI() for c in cert_map.values())))
      self.gctx.checkpoint()
      cb()

    ca_details = self.issue_response_candidate_ca_details

    if True:
      skis_parent = set(x.cert.gSKI()
                        for x in cert_map.itervalues())
      skis_me     = set(x.latest_ca_cert.gSKI()
                        for x in ca_details
                        if x.latest_ca_cert is not None)
      for ski in skis_parent & skis_me:
        rpki.log.debug("Parent %s and I agree that I have SKI %s in resource class %s"
                       % (parent.parent_handle, ski, rc.class_name))
      for ski in skis_parent - skis_me:
        rpki.log.debug("Parent %s thinks I have SKI %s in resource class %s but I don't think so"
                       % (parent.parent_handle, ski, rc.class_name))
      for ski in skis_me - skis_parent:
        rpki.log.debug("I think I have SKI %s in resource class %s but parent %s doesn't think so"
                       % (ski, rc.class_name, parent.parent_handle))

    if ca_details:
      rpki.async.iterator(ca_details, loop, done)
    else:
      rpki.log.warn("Existing resource class %s from parent %s with no certificates, rekeying" % (rc.class_name, parent.parent_handle))
      self.gctx.checkpoint()
      self.rekey(cb, eb)

  @classmethod
  def create(cls, parent, rc, cb, eb):
    """
    Parent has signaled existance of a new resource class, so we need
    to create and set up a corresponding CA object.
    """

    self = cls()
    self.gctx = parent.gctx
    self.parent_id = parent.parent_id
    self.parent_resource_class = rc.class_name
    self.sql_store()
    self.sia_uri = self.construct_sia_uri(parent, rc)
    ca_detail = ca_detail_obj.create(self)

    def done(issue_response):
      ca_detail.activate(
        ca       = self,
        cert     = issue_response.payload.classes[0].certs[0].cert,
        uri      = issue_response.payload.classes[0].certs[0].cert_url,
        callback = cb,
        errback  = eb)

    rpki.up_down.issue_pdu.query(parent, self, ca_detail, done, eb)

  def delete(self, parent, callback):
    """
    The list of current resource classes received from parent does not
    include the class corresponding to this CA, so we need to delete
    it (and its little dog too...).

    All certs published by this CA are now invalid, so need to
    withdraw them, the CRL, and the manifest from the repository,
    delete all child_cert and ca_detail records associated with this
    CA, then finally delete this CA itself.
    """

    def lose(e):
      rpki.log.traceback()
      rpki.log.warn("Could not delete CA %r, skipping: %s" % (self, e))
      callback()

    def done():
      self.sql_delete()      
      callback()

    publisher = publication_queue()
    for ca_detail in self.ca_details:
      ca_detail.delete(ca = self, publisher = publisher)
    publisher.call_pubd(done, lose)

  def next_serial_number(self):
    """
    Allocate a certificate serial number.
    """
    self.last_issued_sn += 1
    self.sql_mark_dirty()
    return self.last_issued_sn

  def next_manifest_number(self):
    """
    Allocate a manifest serial number.
    """
    self.last_manifest_sn += 1
    self.sql_mark_dirty()
    return self.last_manifest_sn

  def next_crl_number(self):
    """
    Allocate a CRL serial number.
    """
    self.last_crl_sn += 1
    self.sql_mark_dirty()
    return self.last_crl_sn

  def rekey(self, cb, eb):
    """
    Initiate a rekey operation for this ca.  Generate a new keypair.
    Request cert from parent using new keypair.  Mark result as our
    active ca_detail.  Reissue all child certs issued by this ca using
    the new ca_detail.
    """

    rpki.log.trace()

    parent = self.parent
    old_detail = self.active_ca_detail
    new_detail = ca_detail_obj.create(self)

    def done(issue_response):
      new_detail.activate(
        ca          = self,
        cert        = issue_response.payload.classes[0].certs[0].cert,
        uri         = issue_response.payload.classes[0].certs[0].cert_url,
        predecessor = old_detail,
        callback    = cb,
        errback     = eb)

    rpki.up_down.issue_pdu.query(parent, self, new_detail, done, eb)

  def revoke(self, cb, eb):
    """
    Revoke deprecated ca_detail objects associated with this ca.
    """

    rpki.log.trace()

    def loop(iterator, ca_detail):
      ca_detail.revoke(cb = iterator, eb = eb)

    rpki.async.iterator(self.deprecated_ca_details, loop, cb)

  def reissue(self, cb, eb):
    """
    Reissue all current certificates issued by this CA.
    """

    ca_detail = self.active_ca_detail
    if ca_detail:
      ca_detail.reissue(cb, eb)
    else:
      cb()

class ca_detail_obj(rpki.sql.sql_persistent):
  """
  Internal CA detail object.
  """

  sql_template = rpki.sql.template(
    "ca_detail",
    "ca_detail_id",
    ("private_key_id",          rpki.x509.RSA),
    ("public_key",              rpki.x509.RSApublic),
    ("latest_ca_cert",          rpki.x509.X509),
    ("manifest_private_key_id", rpki.x509.RSA),
    ("manifest_public_key",     rpki.x509.RSApublic),
    ("latest_manifest_cert",    rpki.x509.X509),
    ("latest_manifest",         rpki.x509.SignedManifest),
    ("latest_crl",              rpki.x509.CRL),
    ("crl_published",           rpki.sundial.datetime),
    ("manifest_published",      rpki.sundial.datetime),
    "state",
    "ca_cert_uri",
    "ca_id")
  
  crl_published = None
  manifest_published = None
  latest_ca_cert = None

  def sql_decode(self, vals):
    """
    Extra assertions for SQL decode of a ca_detail_obj.
    """
    rpki.sql.sql_persistent.sql_decode(self, vals)
    assert self.public_key is None or self.private_key_id is None or self.public_key.get_DER() == self.private_key_id.get_public_DER()
    assert self.manifest_public_key is None or self.manifest_private_key_id is None or self.manifest_public_key.get_DER() == self.manifest_private_key_id.get_public_DER()

  @property
  def ca(self):
    """
    Fetch CA object to which this ca_detail links.
    """
    return ca_obj.sql_fetch(self.gctx, self.ca_id)

  def fetch_child_certs(self, child = None, ski = None, unique = False):
    """
    Fetch all child_cert objects that link to this ca_detail.
    """
    return rpki.rpkid.child_cert_obj.fetch(self.gctx, child, self, ski, unique)

  @property
  def child_certs(self):
    """
    Fetch all child_cert objects that link to this ca_detail.
    """
    return self.fetch_child_certs()

  @property
  def revoked_certs(self):
    """
    Fetch all revoked_cert objects that link to this ca_detail.
    """
    return revoked_cert_obj.sql_fetch_where(self.gctx, "ca_detail_id = %s", (self.ca_detail_id,))

  @property
  def roas(self):
    """
    Fetch all ROA objects that link to this ca_detail.
    """
    return rpki.rpkid.roa_obj.sql_fetch_where(self.gctx, "ca_detail_id = %s", (self.ca_detail_id,))

  @property
  def ghostbusters(self):
    """
    Fetch all Ghostbuster objects that link to this ca_detail.
    """
    return rpki.rpkid.ghostbuster_obj.sql_fetch_where(self.gctx, "ca_detail_id = %s", (self.ca_detail_id,))

  @property
  def crl_uri(self):
    """
    Return publication URI for this ca_detail's CRL.
    """
    return self.ca.sia_uri + self.crl_uri_tail

  @property
  def crl_uri_tail(self):
    """
    Return tail (filename portion) of publication URI for this ca_detail's CRL.
    """
    return self.public_key.gSKI() + ".crl"

  @property
  def manifest_uri(self):
    """
    Return publication URI for this ca_detail's manifest.
    """
    return self.ca.sia_uri + self.public_key.gSKI() + ".mnf"

  def has_expired(self):
    """
    Return whether this ca_detail's certificate has expired.
    """
    return self.latest_ca_cert.getNotAfter() <= rpki.sundial.now()

  def activate(self, ca, cert, uri, callback, errback, predecessor = None):
    """
    Activate this ca_detail.
    """

    publisher = publication_queue()

    self.latest_ca_cert = cert
    self.ca_cert_uri = uri.rsync()
    self.generate_manifest_cert()
    self.state = "active"
    self.generate_crl(publisher = publisher)
    self.generate_manifest(publisher = publisher)
    self.sql_mark_dirty()

    if predecessor is not None:
      predecessor.state = "deprecated"
      predecessor.sql_mark_dirty()
      for child_cert in predecessor.child_certs:
        child_cert.reissue(ca_detail = self, publisher = publisher)
      for roa in predecessor.roas:
        roa.regenerate(publisher = publisher)

      # Need to do something to regenerate ghostbusters here?

    publisher.call_pubd(callback, errback)

  def delete(self, ca, publisher, allow_failure = False):
    """
    Delete this ca_detail and all of the certs it issued.

    If allow_failure is true, we clean up as much as we can but don't
    raise an exception.
    """

    repository = ca.parent.repository
    for child_cert in self.child_certs:
      publisher.withdraw(cls = rpki.publication.certificate_elt, uri = child_cert.uri, obj = child_cert.cert, repository = repository,
                         handler = False if allow_failure else None)
    for roa in self.roas:
      roa.revoke(publisher = publisher, allow_failure = allow_failure)      
    for ghostbuster in self.ghostbusters:
      ghostbuster.revoke(publisher = publisher, allow_failure = allow_failure)
    try:
      latest_manifest = self.latest_manifest
    except AttributeError:
      latest_manifest = None
    if latest_manifest is not None:
      publisher.withdraw(cls = rpki.publication.manifest_elt, uri = self.manifest_uri, obj = self.latest_manifest, repository = repository,
                         handler = False if allow_failure else None)
    try:
      latest_crl = self.latest_crl
    except AttributeError:
      latest_crl = None
    if latest_crl is not None:
      publisher.withdraw(cls = rpki.publication.crl_elt,      uri = self.crl_uri,      obj = self.latest_crl,      repository = repository,
                         handler = False if allow_failure else None)
    for cert in self.child_certs + self.revoked_certs:
      cert.sql_delete()
    self.sql_delete()

  def revoke(self, cb, eb):
    """
    Request revocation of all certificates whose SKI matches the key
    for this ca_detail.

    Tasks:

    - Request revocation of old keypair by parent.

    - Revoke all child certs issued by the old keypair.

    - Generate a final CRL, signed with the old keypair, listing all
      the revoked certs, with a next CRL time after the last cert or
      CRL signed by the old keypair will have expired.

    - Generate a corresponding final manifest.

    - Destroy old keypairs.

    - Leave final CRL and manifest in place until their nextupdate
      time has passed.
    """

    ca = self.ca
    parent = ca.parent

    def parent_revoked(r_msg):

      if r_msg.payload.ski != self.latest_ca_cert.gSKI():
        raise rpki.exceptions.SKIMismatch

      crl_interval = rpki.sundial.timedelta(seconds = parent.self.crl_interval)

      nextUpdate = rpki.sundial.now()

      if self.latest_manifest is not None:
        try:
          self.latest_manifest.get_content()
        except rpki.exceptions.CMSContentNotSet:
          self.latest_manifest.extract()
        nextUpdate = nextUpdate.later(self.latest_manifest.getNextUpdate())

      if self.latest_crl is not None:
        nextUpdate = nextUpdate.later(self.latest_crl.getNextUpdate())

      publisher = publication_queue()

      for child_cert in self.child_certs:
        nextUpdate = nextUpdate.later(child_cert.cert.getNotAfter())
        child_cert.revoke(publisher = publisher)

      for roa in self.roas:
        nextUpdate = nextUpdate.later(roa.cert.getNotAfter())
        roa.revoke(publisher = publisher)

      for ghostbuster in self.ghostbusters:
        nextUpdate = nextUpdate.later(ghostbuster.cert.getNotAfter())
        ghostbuster.revoke(publisher = publisher)

      nextUpdate += crl_interval
      self.generate_crl(publisher = publisher, nextUpdate = nextUpdate)
      self.generate_manifest(publisher = publisher, nextUpdate = nextUpdate)
      self.private_key_id = None
      self.manifest_private_key_id = None
      self.manifest_public_key = None
      self.latest_manifest_cert = None
      self.state = "revoked"
      self.sql_mark_dirty()
      publisher.call_pubd(cb, eb)

    rpki.up_down.revoke_pdu.query(ca, self.latest_ca_cert.gSKI(), parent_revoked, eb)

  def update(self, parent, ca, rc, sia_uri_changed, old_resources, callback, errback):
    """
    Need to get a new certificate for this ca_detail and perhaps frob
    children of this ca_detail.
    """

    def issued(issue_response):
      self.latest_ca_cert = issue_response.payload.classes[0].certs[0].cert
      new_resources = self.latest_ca_cert.get_3779resources()
      publisher = publication_queue()

      if sia_uri_changed or old_resources.oversized(new_resources):
        for child_cert in self.child_certs:
          child_resources = child_cert.cert.get_3779resources()
          if sia_uri_changed or child_resources.oversized(new_resources):
            child_cert.reissue(
              ca_detail = self,
              resources = child_resources.intersection(new_resources),
              publisher = publisher)

      publisher.call_pubd(callback, errback)

    rpki.up_down.issue_pdu.query(parent, ca, self, issued, errback)

  @classmethod
  def create(cls, ca):
    """
    Create a new ca_detail object for a specified CA.
    """
    self = cls()
    self.gctx = ca.gctx
    self.ca_id = ca.ca_id
    self.state = "pending"

    self.private_key_id = rpki.x509.RSA.generate()
    self.public_key = self.private_key_id.get_RSApublic()

    self.manifest_private_key_id = rpki.x509.RSA.generate()
    self.manifest_public_key = self.manifest_private_key_id.get_RSApublic()

    self.sql_store()
    return self

  def issue_ee(self, ca, resources, subject_key, sia = None):
    """
    Issue a new EE certificate.
    """

    return self.latest_ca_cert.issue(
      keypair     = self.private_key_id,
      subject_key = subject_key,
      serial      = ca.next_serial_number(),
      sia         = sia,
      aia         = self.ca_cert_uri,
      crldp       = self.crl_uri,
      resources   = resources,
      notAfter    = self.latest_ca_cert.getNotAfter(),
      is_ca       = False)


  def generate_manifest_cert(self):
    """
    Generate a new manifest certificate for this ca_detail.
    """

    resources = rpki.resource_set.resource_bag.from_inheritance()
    self.latest_manifest_cert = self.issue_ee(self.ca, resources, self.manifest_public_key)

  def issue(self, ca, child, subject_key, sia, resources, publisher, child_cert = None):
    """
    Issue a new certificate to a child.  Optional child_cert argument
    specifies an existing child_cert object to update in place; if not
    specified, we create a new one.  Returns the child_cert object
    containing the newly issued cert.
    """

    assert child_cert is None or (child_cert.child_id == child.child_id and
                                  child_cert.ca_detail_id == self.ca_detail_id)

    cert = self.latest_ca_cert.issue(
      keypair     = self.private_key_id,
      subject_key = subject_key,
      serial      = ca.next_serial_number(),
      aia         = self.ca_cert_uri,
      crldp       = self.crl_uri,
      sia         = sia,
      resources   = resources,
      notAfter    = resources.valid_until)

    if child_cert is None:
      child_cert = rpki.rpkid.child_cert_obj(
        gctx         = child.gctx,
        child_id     = child.child_id,
        ca_detail_id = self.ca_detail_id,
        cert         = cert)
      rpki.log.debug("Created new child_cert %r" % child_cert)
    else:
      child_cert.cert = cert
      rpki.log.debug("Reusing existing child_cert %r" % child_cert)

    child_cert.ski = cert.get_SKI()
    child_cert.published = rpki.sundial.now()
    child_cert.sql_store()
    publisher.publish(
      cls = rpki.publication.certificate_elt,
      uri = child_cert.uri,
      obj = child_cert.cert,
      repository = ca.parent.repository,
      handler = child_cert.published_callback)
    self.generate_manifest(publisher = publisher)
    return child_cert

  def generate_crl(self, publisher, nextUpdate = None):
    """
    Generate a new CRL for this ca_detail.  At the moment this is
    unconditional, that is, it is up to the caller to decide whether a
    new CRL is needed.
    """

    ca = self.ca
    parent = ca.parent
    crl_interval = rpki.sundial.timedelta(seconds = parent.self.crl_interval)
    now = rpki.sundial.now()

    if nextUpdate is None:
      nextUpdate = now + crl_interval

    certlist = []
    for revoked_cert in self.revoked_certs:
      if now > revoked_cert.expires + crl_interval:
        revoked_cert.sql_delete()
      else:
        certlist.append((revoked_cert.serial, revoked_cert.revoked.toASN1tuple(), ()))
    certlist.sort()

    self.latest_crl = rpki.x509.CRL.generate(
      keypair             = self.private_key_id,
      issuer              = self.latest_ca_cert,
      serial              = ca.next_crl_number(),
      thisUpdate          = now,
      nextUpdate          = nextUpdate,
      revokedCertificates = certlist)

    self.crl_published = rpki.sundial.now()
    self.sql_mark_dirty()
    publisher.publish(cls = rpki.publication.crl_elt, uri = self.crl_uri, obj = self.latest_crl, repository = parent.repository,
                      handler = self.crl_published_callback)

  def crl_published_callback(self, pdu):
    """
    Check result of CRL publication.
    """
    pdu.raise_if_error()
    self.crl_published = None
    self.sql_mark_dirty()

  def generate_manifest(self, publisher, nextUpdate = None):
    """
    Generate a new manifest for this ca_detail.
    """

    ca = self.ca
    parent = ca.parent
    crl_interval = rpki.sundial.timedelta(seconds = parent.self.crl_interval)
    now = rpki.sundial.now()

    if nextUpdate is None:
      nextUpdate = now + crl_interval

    if self.latest_manifest_cert is None or self.latest_manifest_cert.getNotAfter() < nextUpdate:
      self.generate_manifest_cert()

    objs = [(self.crl_uri_tail, self.latest_crl)]
    objs.extend((c.uri_tail, c.cert) for c in self.child_certs)
    objs.extend((r.uri_tail, r.roa) for r in self.roas if r.roa is not None)
    objs.extend((g.uri_tail, g.ghostbuster) for g in self.ghostbusters)

    self.latest_manifest = rpki.x509.SignedManifest.build(
      serial         = ca.next_manifest_number(),
      thisUpdate     = now,
      nextUpdate     = nextUpdate,
      names_and_objs = objs,
      keypair        = self.manifest_private_key_id,
      certs          = self.latest_manifest_cert)


    self.manifest_published = rpki.sundial.now()
    self.sql_mark_dirty()
    publisher.publish(cls = rpki.publication.manifest_elt, uri = self.manifest_uri, obj = self.latest_manifest, repository = parent.repository,
                      handler = self.manifest_published_callback)

  def manifest_published_callback(self, pdu):
    """
    Check result of manifest publication.
    """
    pdu.raise_if_error()
    self.manifest_published = None
    self.sql_mark_dirty()

  def reissue(self, cb, eb):
    """
    Reissue all current certificates issued by this ca_detail.
    """

    publisher = publication_queue()
    for roa in self.roas:
      roa.regenerate(publisher, fast = True)
    for ghostbuster in self.ghostbusters:
      ghostbuster.regenerate(publisher, fast = True)
    for child_cert in self.child_certs:
      child_cert.reissue(self, publisher, force = True)
    publisher.call_pubd(cb, eb)

class child_cert_obj(rpki.sql.sql_persistent):
  """
  Certificate that has been issued to a child.
  """

  sql_template = rpki.sql.template(
    "child_cert",
    "child_cert_id",
    ("cert", rpki.x509.X509),
    "child_id",
    "ca_detail_id",
    "ski",
    ("published", rpki.sundial.datetime))

  def __init__(self, gctx = None, child_id = None, ca_detail_id = None, cert = None):
    """
    Initialize a child_cert_obj.
    """
    rpki.sql.sql_persistent.__init__(self)
    self.gctx = gctx
    self.child_id = child_id
    self.ca_detail_id = ca_detail_id
    self.cert = cert
    self.published = None
    if child_id or ca_detail_id or cert:
      self.sql_mark_dirty()

  @property
  def child(self):
    """
    Fetch child object to which this child_cert object links.
    """
    return rpki.left_right.child_elt.sql_fetch(self.gctx, self.child_id)

  @property
  def ca_detail(self):
    """
    Fetch ca_detail object to which this child_cert object links.
    """
    return ca_detail_obj.sql_fetch(self.gctx, self.ca_detail_id)

  @property
  def uri_tail(self):
    """
    Return the tail (filename) portion of the URI for this child_cert.
    """
    return self.cert.gSKI() + ".cer"

  @property
  def uri(self):
    """
    Return the publication URI for this child_cert.
    """
    return self.ca_detail.ca.sia_uri + self.uri_tail

  def revoke(self, publisher, generate_crl_and_manifest = False):
    """
    Revoke a child cert.
    """

    ca_detail = self.ca_detail
    ca = ca_detail.ca
    rpki.log.debug("Revoking %r %r" % (self, self.uri))
    revoked_cert_obj.revoke(cert = self.cert, ca_detail = ca_detail)
    publisher.withdraw(cls = rpki.publication.certificate_elt, uri = self.uri, obj = self.cert, repository = ca.parent.repository)
    self.gctx.sql.sweep()
    self.sql_delete()
    if generate_crl_and_manifest:
      ca_detail.generate_crl(publisher = publisher)
      ca_detail.generate_manifest(publisher = publisher)

  def reissue(self, ca_detail, publisher, resources = None, sia = None, force = False):
    """
    Reissue an existing child cert, reusing the public key.  If the
    child cert we would generate is identical to the one we already
    have, we just return the one we already have.  If we have to
    revoke the old child cert when generating the new one, we have to
    generate a new child_cert_obj, so calling code that needs the
    updated child_cert_obj must use the return value from this method.
    """

    ca = ca_detail.ca
    child = self.child

    old_resources = self.cert.get_3779resources()
    old_sia       = self.cert.get_SIA()
    old_ca_detail = self.ca_detail

    needed = False

    if resources is None:
      resources = old_resources

    if sia is None:
      sia = old_sia

    assert resources.valid_until is not None and old_resources.valid_until is not None

    if resources != old_resources:
      rpki.log.debug("Resources changed for %r" % self)
      needed = True

    if sia != old_sia:
      rpki.log.debug("SIA changed for %r" % self)
      needed = True

    if ca_detail != old_ca_detail:
      rpki.log.debug("Issuer changed for %r" % self)
      needed = True

    must_revoke = old_resources.oversized(resources) or old_resources.valid_until > resources.valid_until
    if must_revoke:
      rpki.log.debug("Must revoke any existing cert(s) for %r" % self)
      needed = True

    new_issuer = ca_detail != old_ca_detail
    if new_issuer:
      rpki.log.debug("Issuer changed for %r" % self)
      needed = True

    if resources.valid_until != old_resources.valid_until:
      rpki.log.debug("Validity changed for %r: %s %s" % (self, old_resources.valid_until, resources.valid_until))
      needed = True

    if not needed and force:
      rpki.log.debug("No change needed for %r, forcing reissuance anyway" % self)
      needed = True

    if not needed:
      rpki.log.debug("No change to %r" % self)
      return self

    if must_revoke:
      for x in child.fetch_child_certs(ca_detail = ca_detail, ski = self.ski):
        rpki.log.debug("Revoking child_cert %r" % x)
        x.revoke(publisher = publisher)
      ca_detail.generate_crl(publisher = publisher)
      ca_detail.generate_manifest(publisher = publisher)

    child_cert = ca_detail.issue(
      ca          = ca,
      child       = child,
      subject_key = self.cert.getPublicKey(),
      sia         = sia,
      resources   = resources,
      child_cert  = None if must_revoke or new_issuer else self,
      publisher   = publisher)

    rpki.log.debug("New child_cert %r uri %s" % (child_cert, child_cert.uri))

    return child_cert

  @classmethod
  def fetch(cls, gctx = None, child = None, ca_detail = None, ski = None, unique = False):
    """
    Fetch all child_cert objects matching a particular set of
    parameters.  This is a wrapper to consolidate various queries that
    would otherwise be inline SQL WHERE expressions.  In most cases
    code calls this indirectly, through methods in other classes.
    """

    args = []
    where = []

    if child:
      where.append("child_id = %s")
      args.append(child.child_id)

    if ca_detail:
      where.append("ca_detail_id = %s")
      args.append(ca_detail.ca_detail_id)

    if ski:
      where.append("ski = %s")
      args.append(ski)

    where = " AND ".join(where)

    gctx = gctx or (child and child.gctx) or (ca_detail and ca_detail.gctx) or None

    if unique:
      return cls.sql_fetch_where1(gctx, where, args)
    else:
      return cls.sql_fetch_where(gctx, where, args)

  def published_callback(self, pdu):
    """
    Publication callback: check result and mark published.
    """
    pdu.raise_if_error()
    self.published = None
    self.sql_mark_dirty()

class revoked_cert_obj(rpki.sql.sql_persistent):
  """
  Tombstone for a revoked certificate.
  """

  sql_template = rpki.sql.template(
    "revoked_cert",
    "revoked_cert_id",
    "serial",
    "ca_detail_id",
    ("revoked", rpki.sundial.datetime),
    ("expires", rpki.sundial.datetime))

  def __init__(self, gctx = None, serial = None, revoked = None, expires = None, ca_detail_id = None):
    """
    Initialize a revoked_cert_obj.
    """
    rpki.sql.sql_persistent.__init__(self)
    self.gctx = gctx
    self.serial = serial
    self.revoked = revoked
    self.expires = expires
    self.ca_detail_id = ca_detail_id
    if serial or revoked or expires or ca_detail_id:
      self.sql_mark_dirty()

  @property
  def ca_detail(self):
    """
    Fetch ca_detail object to which this revoked_cert_obj links.
    """
    return ca_detail_obj.sql_fetch(self.gctx, self.ca_detail_id)

  @classmethod
  def revoke(cls, cert, ca_detail):
    """
    Revoke a certificate.
    """
    return cls(
      serial       = cert.getSerial(),
      expires      = cert.getNotAfter(),
      revoked      = rpki.sundial.now(),
      gctx         = ca_detail.gctx,
      ca_detail_id = ca_detail.ca_detail_id)

class roa_obj(rpki.sql.sql_persistent):
  """
  Route Origin Authorization.
  """

  sql_template = rpki.sql.template(
    "roa",
    "roa_id",
    "ca_detail_id",
    "self_id",
    "asn",
    ("roa", rpki.x509.ROA),
    ("cert", rpki.x509.X509),
    ("published", rpki.sundial.datetime))

  ca_detail_id = None
  cert = None
  roa = None
  published = None

  @property
  def self(self):
    """
    Fetch self object to which this roa_obj links.
    """
    return rpki.left_right.self_elt.sql_fetch(self.gctx, self.self_id)

  @property
  def ca_detail(self):
    """
    Fetch ca_detail object to which this roa_obj links.
    """
    return rpki.rpkid.ca_detail_obj.sql_fetch(self.gctx, self.ca_detail_id)

  def sql_fetch_hook(self):
    """
    Extra SQL fetch actions for roa_obj -- handle prefix lists.
    """
    for version, datatype, attribute in ((4, rpki.resource_set.roa_prefix_set_ipv4, "ipv4"),
                                         (6, rpki.resource_set.roa_prefix_set_ipv6, "ipv6")):
      setattr(self, attribute, datatype.from_sql(
        self.gctx.sql,
        """
            SELECT prefix, prefixlen, max_prefixlen FROM roa_prefix
            WHERE roa_id = %s AND version = %s
        """,
        (self.roa_id, version)))

  def sql_insert_hook(self):
    """
    Extra SQL insert actions for roa_obj -- handle prefix lists.
    """
    for version, prefix_set in ((4, self.ipv4), (6, self.ipv6)):
      if prefix_set:
        self.gctx.sql.executemany(
          """
            INSERT roa_prefix (roa_id, prefix, prefixlen, max_prefixlen, version)
            VALUES (%s, %s, %s, %s, %s)
          """,
          ((self.roa_id, x.prefix, x.prefixlen, x.max_prefixlen, version)
           for x in prefix_set))

  def sql_delete_hook(self):
    """
    Extra SQL delete actions for roa_obj -- handle prefix lists.
    """
    self.gctx.sql.execute("DELETE FROM roa_prefix WHERE roa_id = %s", (self.roa_id,))

  def __repr__(self):
    v4 = "" if self.ipv4 is None else self.ipv4
    v6 = "" if self.ipv6 is None else self.ipv6
    return rpki.log.log_repr(self, self.asn, ("%s,%s" % (v4, v6)).strip(","))

  def __init__(self, gctx = None, self_id = None, asn = None, ipv4 = None, ipv6 = None):
    rpki.sql.sql_persistent.__init__(self)
    self.gctx = gctx
    self.self_id = self_id
    self.asn = asn
    self.ipv4 = ipv4
    self.ipv6 = ipv6

    # Defer marking new ROA as dirty until .generate() has a chance to
    # finish setup, otherwise we get SQL consistency errors.
    #
    #if self_id or asn or ipv4 or ipv6: self.sql_mark_dirty()

  def update(self, publisher, fast = False):
    """
    Bring this roa_obj's ROA up to date if necesssary.
    """

    v4 = self.ipv4.to_resource_set() if self.ipv4 is not None else rpki.resource_set.resource_set_ipv4()
    v6 = self.ipv6.to_resource_set() if self.ipv6 is not None else rpki.resource_set.resource_set_ipv6()

    if self.roa is None:
      rpki.log.debug("%r doesn't exist, generating" % self)
      return self.generate(publisher = publisher, fast = fast)

    ca_detail = self.ca_detail

    if ca_detail is None:
      rpki.log.debug("%r has no associated ca_detail, generating" % self)
      return self.generate(publisher = publisher, fast = fast)

    if ca_detail.state != "active":
      rpki.log.debug("ca_detail associated with %r not active (state %s), regenerating" % (self, ca_detail.state))
      return self.regenerate(publisher = publisher, fast = fast)

    regen_time = self.cert.getNotAfter() - rpki.sundial.timedelta(seconds = self.self.regen_margin)

    if rpki.sundial.now() > regen_time:
      rpki.log.debug("%r past threshold %s, regenerating" % (self, regen_time))
      return self.regenerate(publisher = publisher, fast = fast)

    ca_resources = ca_detail.latest_ca_cert.get_3779resources()
    ee_resources = self.cert.get_3779resources()

    if ee_resources.oversized(ca_resources):
      rpki.log.debug("%r oversized with respect to CA, regenerating" % self)
      return self.regenerate(publisher = publisher, fast = fast)

    if ee_resources.v4 != v4 or ee_resources.v6 != v6:
      rpki.log.debug("%r resources do not match EE, regenerating" % self)
      return self.regenerate(publisher = publisher, fast = fast)

  def generate(self, publisher, fast = False):
    """
    Generate a ROA.

    At present we have no way of performing a direct lookup from a
    desired set of resources to a covering certificate, so we have to
    search.  This could be quite slow if we have a lot of active
    ca_detail objects.  Punt on the issue for now, revisit if
    profiling shows this as a hotspot.

    Once we have the right covering certificate, we generate the ROA
    payload, generate a new EE certificate, use the EE certificate to
    sign the ROA payload, publish the result, then throw away the
    private key for the EE cert, all per the ROA specification.  This
    implies that generating a lot of ROAs will tend to thrash
    /dev/random, but there is not much we can do about that.

    If fast is set, we leave generating the new manifest for our
    caller to handle, presumably at the end of a bulk operation.
    """

    if self.ipv4 is None and self.ipv6 is None:
      raise rpki.exceptions.EmptyROAPrefixList

    # Ugly and expensive search for covering ca_detail, there has to
    # be a better way, but it would require the ability to test for
    # resource subsets in SQL.

    v4 = self.ipv4.to_resource_set() if self.ipv4 is not None else rpki.resource_set.resource_set_ipv4()
    v6 = self.ipv6.to_resource_set() if self.ipv6 is not None else rpki.resource_set.resource_set_ipv6()

    ca_detail = self.ca_detail
    if ca_detail is None or ca_detail.state != "active" or ca_detail.has_expired():
      ca_detail = None
      for parent in self.self.parents:
        for ca in parent.cas:
          ca_detail = ca.active_ca_detail
          if ca_detail is not None and not ca_detail.has_expired():
            resources = ca_detail.latest_ca_cert.get_3779resources()
            if v4.issubset(resources.v4) and v6.issubset(resources.v6):
              break
          ca_detail = None
        if ca_detail is not None:
          break

    if ca_detail is None:
      raise rpki.exceptions.NoCoveringCertForROA, "Could not find a certificate covering %r" % self

    ca = ca_detail.ca
    resources = rpki.resource_set.resource_bag(v4 = v4, v6 = v6)
    keypair = rpki.x509.RSA.generate()

    self.ca_detail_id = ca_detail.ca_detail_id
    self.cert = ca_detail.issue_ee(
      ca          = ca,
      resources   = resources,
      subject_key = keypair.get_RSApublic(),
      sia         = ((rpki.oids.name2oid["id-ad-signedObject"], ("uri", self.uri_from_key(keypair))),))
    self.roa = rpki.x509.ROA.build(self.asn, self.ipv4, self.ipv6, keypair, (self.cert,))
    self.published = rpki.sundial.now()
    self.sql_store()

    rpki.log.debug("Generating %r URI %s" % (self, self.uri))
    publisher.publish(cls = rpki.publication.roa_elt, uri = self.uri, obj = self.roa, repository = ca.parent.repository, handler = self.published_callback)
    if not fast:
      ca_detail.generate_manifest(publisher = publisher)

  def published_callback(self, pdu):
    """
    Check publication result.
    """
    pdu.raise_if_error()
    self.published = None
    self.sql_mark_dirty()

  def revoke(self, publisher, regenerate = False, allow_failure = False, fast = False):
    """
    Withdraw ROA associated with this roa_obj.

    In order to preserve make-before-break properties without
    duplicating code, this method also handles generating a
    replacement ROA when requested.

    If allow_failure is set, failing to withdraw the ROA will not be
    considered an error.

    If fast is set, SQL actions will be deferred, on the assumption
    that our caller will handle regenerating CRL and manifest and
    flushing the SQL cache.
    """

    ca_detail = self.ca_detail
    cert = self.cert
    roa = self.roa
    uri = self.uri

    if ca_detail.state != 'active':
      self.ca_detail_id = None

    if regenerate:
      self.generate(publisher = publisher, fast = fast)

    rpki.log.debug("Withdrawing %r %s and revoking its EE cert" % (self, uri))
    rpki.rpkid.revoked_cert_obj.revoke(cert = cert, ca_detail = ca_detail)
    publisher.withdraw(cls = rpki.publication.roa_elt, uri = uri, obj = roa, repository = ca_detail.ca.parent.repository,
                       handler = False if allow_failure else None)
    self.sql_mark_deleted()
    if not fast:
      ca_detail.generate_crl(publisher = publisher)
      ca_detail.generate_manifest(publisher = publisher)
      self.gctx.sql.sweep()

  def regenerate(self, publisher, fast = False):
    """
    Reissue ROA associated with this roa_obj.
    """
    if self.ca_detail is None:
      self.generate(publisher = publisher, fast = fast)
    else:
      self.revoke(publisher = publisher, regenerate = True, fast = fast)

  def uri_from_key(self, key):
    """
    Return publication URI for a public key.
    """
    return self.ca_detail.ca.sia_uri + key.gSKI() + ".roa"

  @property
  def uri(self):
    """
    Return the publication URI for this roa_obj's ROA.
    """
    return self.ca_detail.ca.sia_uri + self.uri_tail

  @property
  def uri_tail(self):
    """
    Return the tail (filename portion) of the publication URI for this
    roa_obj's ROA.
    """
    return self.cert.gSKI() + ".roa"


class ghostbuster_obj(rpki.sql.sql_persistent):
  """
  Ghostbusters record.
  """

  sql_template = rpki.sql.template(
    "ghostbuster",
    "ghostbuster_id",
    "ca_detail_id",
    "self_id",
    "vcard",
    ("ghostbuster", rpki.x509.Ghostbuster),
    ("cert", rpki.x509.X509),
    ("published", rpki.sundial.datetime))

  ca_detail_id = None
  cert = None
  ghostbuster = None
  published = None
  vcard = None

  @property
  def self(self):
    """
    Fetch self object to which this ghostbuster_obj links.
    """
    return rpki.left_right.self_elt.sql_fetch(self.gctx, self.self_id)

  @property
  def ca_detail(self):
    """
    Fetch ca_detail object to which this ghostbuster_obj links.
    """
    return rpki.rpkid.ca_detail_obj.sql_fetch(self.gctx, self.ca_detail_id)

  def __init__(self, gctx = None, self_id = None, ca_detail_id = None, vcard = None):
    rpki.sql.sql_persistent.__init__(self)
    self.gctx = gctx
    self.self_id = self_id
    self.ca_detail_id = ca_detail_id
    self.vcard = vcard

    # Defer marking new ghostbuster as dirty until .generate() has a chance to
    # finish setup, otherwise we get SQL consistency errors.

  def update(self, publisher, fast = False):
    """
    Bring this ghostbuster_obj up to date if necesssary.
    """

    if self.ghostbuster is None:
      rpki.log.debug("Ghostbuster record doesn't exist, generating")
      return self.generate(publisher = publisher, fast = fast)

    regen_time = self.cert.getNotAfter() - rpki.sundial.timedelta(seconds = self.self.regen_margin)

    if rpki.sundial.now() > regen_time:
      rpki.log.debug("Ghostbuster record past threshold %s, regenerating" % (regen_time,))
      return self.regenerate(publisher = publisher, fast = fast)

  def generate(self, publisher, fast = False):
    """
    Generate a Ghostbuster record

    Once we have the right covering certificate, we generate the
    ghostbuster payload, generate a new EE certificate, use the EE
    certificate to sign the ghostbuster payload, publish the result,
    then throw away the private key for the EE cert.  This is modeled
    after the way we handle ROAs.

    If fast is set, we leave generating the new manifest for our
    caller to handle, presumably at the end of a bulk operation.
    """

    ca_detail = self.ca_detail
    ca = ca_detail.ca

    resources = rpki.resource_set.resource_bag.from_inheritance()
    keypair = rpki.x509.RSA.generate()

    self.cert = ca_detail.issue_ee(
      ca          = ca,
      resources   = resources,
      subject_key = keypair.get_RSApublic(),
      sia         = ((rpki.oids.name2oid["id-ad-signedObject"], ("uri", self.uri_from_key(keypair))),))
    self.ghostbuster = rpki.x509.Ghostbuster.build(self.vcard, keypair, (self.cert,))
    self.published = rpki.sundial.now()
    self.sql_store()

    rpki.log.debug("Generating Ghostbuster record %r" % self.uri)
    publisher.publish(cls = rpki.publication.ghostbuster_elt, uri = self.uri, obj = self.ghostbuster, repository = ca.parent.repository, handler = self.published_callback)
    if not fast:
      ca_detail.generate_manifest(publisher = publisher)

  def published_callback(self, pdu):
    """
    Check publication result.
    """
    pdu.raise_if_error()
    self.published = None
    self.sql_mark_dirty()

  def revoke(self, publisher, regenerate = False, allow_failure = False, fast = False):
    """
    Withdraw Ghostbuster associated with this ghostbuster_obj.

    In order to preserve make-before-break properties without
    duplicating code, this method also handles generating a
    replacement ghostbuster when requested.

    If allow_failure is set, failing to withdraw the ghostbuster will not be
    considered an error.

    If fast is set, SQL actions will be deferred, on the assumption
    that our caller will handle regenerating CRL and manifest and
    flushing the SQL cache.
    """

    ca_detail = self.ca_detail
    cert = self.cert
    ghostbuster = self.ghostbuster
    uri = self.uri

    if regenerate:
      assert ca_detail.state == 'active'
      self.generate(publisher = publisher, fast = fast)

    rpki.log.debug("Withdrawing Ghostbuster record %r and revoking its EE cert" % uri)
    rpki.rpkid.revoked_cert_obj.revoke(cert = cert, ca_detail = ca_detail)
    publisher.withdraw(cls = rpki.publication.ghostbuster_elt, uri = uri, obj = ghostbuster, repository = ca_detail.ca.parent.repository,
                       handler = False if allow_failure else None)
    self.sql_mark_deleted()
    if not fast:
      ca_detail.generate_crl(publisher = publisher)
      ca_detail.generate_manifest(publisher = publisher)
      self.gctx.sql.sweep()

  def regenerate(self, publisher, fast = False):
    """
    Reissue Ghostbuster associated with this ghostbuster_obj.
    """
    if self.ghostbuster is None:
      self.generate(publisher = publisher, fast = fast)
    else:
      self.revoke(publisher = publisher, regenerate = True, fast = fast)

  def uri_from_key(self, key):
    """
    Return publication URI for a public key.
    """
    return self.ca_detail.ca.sia_uri + key.gSKI() + ".gbr"

  @property
  def uri(self):
    """
    Return the publication URI for this ghostbuster_obj's ghostbuster.
    """
    return self.ca_detail.ca.sia_uri + self.uri_tail

  @property
  def uri_tail(self):
    """
    Return the tail (filename portion) of the publication URI for this
    ghostbuster_obj's ghostbuster.
    """
    return self.cert.gSKI() + ".gbr"


class publication_queue(object):
  """
  Utility to simplify publication from within rpkid.

  General idea here is to accumulate a collection of objects to be
  published, in one or more repositories, each potentially with its
  own completion callback.  Eventually we want to publish everything
  we've accumulated, at which point we need to iterate over the
  collection and do repository.call_pubd() for each repository.
  """

  replace = True

  def __init__(self):
    self.repositories = {}
    self.msgs = {}
    self.handlers = {}
    if self.replace:
      self.uris = {}

  def _add(self, uri, obj, repository, handler, make_pdu):
    rid = id(repository)
    if rid not in self.repositories:
      self.repositories[rid] = repository
      self.msgs[rid] = rpki.publication.msg.query()
    if self.replace and uri in self.uris:
      rpki.log.debug("Removing publication duplicate <%s %r %r>" % (self.uris[uri].action, self.uris[uri].uri, self.uris[uri].payload))
      self.msgs[rid].remove(self.uris.pop(uri))
    pdu = make_pdu(uri = uri, obj = obj)
    if handler is not None:
      self.handlers[id(pdu)] = handler
      pdu.tag = id(pdu)
    self.msgs[rid].append(pdu)
    if self.replace:
      self.uris[uri] = pdu

  def publish(self,  cls, uri, obj, repository, handler = None):
    return self._add(     uri, obj, repository, handler, cls.make_publish)

  def withdraw(self, cls, uri, obj, repository, handler = None):
    return self._add(     uri, obj, repository, handler, cls.make_withdraw)

  def call_pubd(self, cb, eb):
    def loop(iterator, rid):
      self.repositories[rid].call_pubd(iterator, eb, self.msgs[rid], self.handlers)
    rpki.async.iterator(self.repositories, loop, cb)
