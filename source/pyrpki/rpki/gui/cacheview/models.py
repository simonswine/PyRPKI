"""
Copyright (C) 2011  SPARTA, Inc. dba Cobham Analytic Solutions

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

from datetime import datetime
import time

from django.db import models

from rpki.resource_set import resource_range_ipv4, resource_range_ipv6
from rpki.exceptions import MustBePrefix

class TelephoneField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 255
        models.CharField.__init__(self, *args, **kwargs)

class AddressRange(models.Model):
    family = models.IntegerField()
    min = models.IPAddressField(db_index=True)
    max = models.IPAddressField(db_index=True)

    class Meta:
        ordering = ('family', 'min', 'max')
        unique_together = ('family', 'min', 'max')

    @models.permalink
    def get_absolute_url(self):
        return ('rpki.gui.cacheview.views.addressrange_detail', [str(self.pk)])

    def __unicode__(self):
        if self.min == self.max:
            return u'%s' % self.min

        if self.family == 4:
            r = resource_range_ipv4.from_strings(self.min, self.max)
        elif self.family == 6:
            r = resource_range_ipv6.from_strings(self.min, self.max)

        try:
            prefixlen = r.prefixlen()
        except MustBePrefix:
            return u'%s-%s' % (self.min, self.max)
        return u'%s/%d' % (self.min, prefixlen)

class ASRange(models.Model):
    min = models.PositiveIntegerField(db_index=True)
    max = models.PositiveIntegerField(db_index=True)

    class Meta:
        ordering = ('min', 'max')
        #unique_together = ('min', 'max')

    def __unicode__(self):
        if self.min == self.max:
            return u'AS%d' % self.min
        else:
            return u'AS%s-%s' % (self.min, self.max)

    @models.permalink
    def get_absolute_url(self):
        return ('rpki.gui.cacheview.views.asrange_detail', [str(self.pk)])

kinds = list(enumerate(('good', 'warn', 'bad')))
kinds_dict = dict((v,k) for k,v in kinds)

class ValidationLabel(models.Model):
    """
    Represents a specific error condition defined in the rcynic XML
    output file.
    """
    label = models.CharField(max_length=30, db_index=True, unique=True)
    status = models.CharField(max_length=255)
    kind = models.PositiveSmallIntegerField(choices=kinds)

    def __unicode__(self):
        return self.label

    class Meta:
        verbose_name_plural = 'ValidationLabels'

generations = list(enumerate(('current', 'backup')))
generations_dict = dict((val, key) for (key, val) in generations)

class ValidationStatus(models.Model):
    timestamp  = models.DateTimeField()
    generation = models.PositiveSmallIntegerField(choices=generations, null=True)
    status     = models.ForeignKey('ValidationLabel')

    class Meta:
        abstract = True

class SignedObject(models.Model):
    """
    Abstract class to hold common metadata for all signed objects.
    The signing certificate is ommitted here in order to give a proper
    value for the 'related_name' attribute.
    """
    # attributes from rcynic's output XML file
    uri        = models.URLField(unique=True, db_index=True)

    # on-disk file modification time
    mtime      = models.PositiveIntegerField(default=0)

    # SubjectName
    name  = models.CharField(max_length=255)

    # value from the SKI extension
    keyid = models.CharField(max_length=50, db_index=True)

    # validity period from EE cert which signed object
    not_before = models.DateTimeField()
    not_after  = models.DateTimeField()

    class Meta:
        abstract = True

    def mtime_as_datetime(self):
        """
        convert the local timestamp to UTC and convert to a datetime object
        """
        return datetime.utcfromtimestamp(self.mtime + time.timezone)

    def is_valid(self):
        """
        Returns a boolean value indicating whether this object has passed
        validation checks.
        """
        return bool(self.statuses.filter(status=ValidationLabel.objects.get(label="object_accepted")))

    def status_id(self):
        """
        Returns a HTML class selector for the current object based on its validation status.
        The selector is chosen based on the current generation only.  If there is any bad status,
        return bad, else if there are any warn status, return warn, else return good.
        """
        for x in reversed(kinds):
            if self.statuses.filter(generation=generations_dict['current'], status__kind=x[0]):
                return x[1]
        return None # should not happen

    def __unicode__(self):
        return u'%s' % self.name

class Cert(SignedObject):
    """
    Object representing a resource certificate.
    """
    addresses = models.ManyToManyField(AddressRange, related_name='certs')
    asns      = models.ManyToManyField(ASRange, related_name='certs')
    issuer    = models.ForeignKey('Cert', related_name='children', null=True, blank=True)
    sia       = models.CharField(max_length=255)

    @models.permalink
    def get_absolute_url(self):
        return ('rpki.gui.cacheview.views.cert_detail', [str(self.pk)])

class ValidationStatus_Cert(ValidationStatus):
    cert = models.ForeignKey('Cert', related_name='statuses')

class ROAPrefix(models.Model):
    family     = models.PositiveIntegerField()
    prefix     = models.IPAddressField()
    bits       = models.PositiveIntegerField()
    max_length = models.PositiveIntegerField()

    class Meta:
        ordering = ['family', 'prefix', 'bits', 'max_length']

    def __unicode__(self):
        if self.bits == self.max_length:
            return u'%s/%d' % (self.prefix, self.bits)
        else:
            return u'%s/%d-%d' % (self.prefix, self.bits, self.max_length)

class ROA(SignedObject):
    asid     = models.PositiveIntegerField()
    prefixes = models.ManyToManyField(ROAPrefix, related_name='roas')
    issuer   = models.ForeignKey('Cert', related_name='roas')

    @models.permalink
    def get_absolute_url(self):
        return ('rpki.gui.cacheview.views.roa_detail', [str(self.pk)])

    class Meta:
        ordering = ['asid']

    def __unicode__(self):
        return u'ROA for AS%d' % self.asid

    @models.permalink
    def get_absolute_url(self):
        return ('rpki.gui.cacheview.views.roa_detail', [str(self.pk)])

class ValidationStatus_ROA(ValidationStatus):
    roa = models.ForeignKey('ROA', related_name='statuses')

class Ghostbuster(SignedObject):
    full_name     = models.CharField(max_length=40)
    email_address = models.EmailField(blank=True, null=True)
    organization  = models.CharField(blank=True, null=True, max_length=255)
    telephone     = TelephoneField(blank=True, null=True)
    issuer        = models.ForeignKey('Cert', related_name='ghostbusters')

    @models.permalink
    def get_absolute_url(self):
        return ('rpki.gui.cacheview.views.ghostbuster_detail', [str(self.pk)])

    def __unicode__(self):
        if self.full_name:
            return self.full_name
        if self.organization:
            return self.organization
        if self.email_address:
            return self.email_address
        return self.telephone

class ValidationStatus_Ghostbuster(ValidationStatus):
    gbr = models.ForeignKey('Ghostbuster', related_name='statuses')

# vim:sw=4 ts=8 expandtab
