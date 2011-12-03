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

from django.views.generic import list_detail
from django.shortcuts import get_object_or_404, redirect

from rpki.gui.cacheview import models, forms, misc
from rpki.gui.app.views import render
from rpki.resource_set import resource_range_as
from rpki.ipaddrs import v4addr, v6addr

# Create your views here.

def cert_chain(obj):
    """
    returns an iterator covering all certs from the root cert down to the EE.
    """
    chain = []
    while obj:
        chain.append(obj)
        obj = obj.issuer
    return zip(range(len(chain)), reversed(chain))

def signed_object_detail(request, model_class, pk):
    """
    wrapper around object_detail which fetches the x.509 cert chain for signed
    objects.
    """
    obj = get_object_or_404(model_class, pk=pk)
    return list_detail.object_detail(request, queryset=model_class.objects.all(),
            object_id=pk, extra_context={ 'chain': cert_chain(obj) })

def addressrange_detail(request, pk):
    return list_detail.object_detail(request, models.AddressRange.objects.all(), pk)

def asrange_detail(request, pk):
    return list_detail.object_detail(request, models.ASRange.objects.all(), pk)

def roa_detail(request, pk):
    return signed_object_detail(request, models.ROA, pk)

def cert_detail(request, pk):
    return signed_object_detail(request, models.Cert, pk)

def ghostbuster_detail(request, pk):
    return signed_object_detail(request, models.Ghostbuster, pk)

def search_view(request):
    if request.method == 'POST':
        form = forms.SearchForm(request.POST, request.FILES)
        if form.is_valid():
            certs = None
            roas = None

            addr = form.cleaned_data.get('addr')
            asn = form.cleaned_data.get('asn')

            if addr:
                family, r = misc.parse_ipaddr(addr)
                certs = models.Cert.objects.filter(addresses__family=family, addresses__min=str(r.min), addresses__max=str(r.max))
                roas = models.ROA.objects.filter(prefixes__family=family, prefixes__prefix=str(r.min))
            elif asn:
                r = resource_range_as.parse_str(asn)
                certs = models.Cert.objects.filter(asns__min__gte=r.min, asns__max__lte=r.max)
                roas = models.ROA.objects.filter(asid__gte=r.min, asid__lte=r.max)

            return render('cacheview/search_result.html', { 'certs': certs, 'roas': roas }, request)
    else:
        form = forms.SearchForm()

    return render('cacheview/search_form.html', { 'form': form, 'search_type': 'Resource' }, request)

def cmp_prefix(x,y):
    r = cmp(x[0].family, y[0].family)
    if r == 0:
        r = cmp(x[2], y[2]) # integer address
        if r == 0:
            r = cmp(x[0].bits, y[0].bits)
            if r == 0:
                r = cmp(x[0].max_length, y[0].max_length)
                if r == 0:
                    r = cmp(x[1].asid, y[1].asid)
    return r

#def cmp_prefix(x,y):
#    for attr in ('family', 'prefix', 'bits', 'max_length'):
#        r = cmp(getattr(x[0], attr), getattr(y[0], attr))
#        if r:
#            return r
#    return cmp(x[1].asid, y[1].asid)
    
def query_view(request):
    """
    Allow the user to search for an AS or prefix, and show all published ROA
    information.
    """

    if request.method == 'POST':
        form = forms.SearchForm(request.POST, request.FILES)
        if form.is_valid():
            certs = None
            roas = None

            addr = form.cleaned_data.get('addr')
            asn = form.cleaned_data.get('asn')

            if addr:
                family, r = misc.parse_ipaddr(addr)
                prefixes = models.ROAPrefix.objects.filter(family=family, prefix=str(r.min))

                prefix_list = []
                for pfx in prefixes:
                    for roa in pfx.roas.all():
                        prefix_list.append((pfx, roa))
            elif asn:
                r = resource_range_as.parse_str(asn)
                roas = models.ROA.objects.filter(asid__gte=r.min, asid__lte=r.max)

                # display the results sorted by prefix
                prefix_list = []
                for roa in roas:
                    for pfx in roa.prefixes.all():
                        if pfx.family == 4:
                            addr = v4addr(pfx.prefix.encode())
                        elif pfx.family == 6:
                            addr = v6addr(pfx.prefix.encode())

                        prefix_list.append((pfx, roa, addr))
                prefix_list.sort(cmp=cmp_prefix)

            return render('cacheview/query_result.html',
                    { 'object_list': prefix_list }, request)
    else:
        form = forms.SearchForm()

    return render('cacheview/search_form.html', { 'form':form, 'search_type': 'ROA ' }, request)

# vim:sw=4 ts=8 expandtab
