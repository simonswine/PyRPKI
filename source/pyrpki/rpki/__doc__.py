## @file
# @details
# Documentation sourc, expressed as Python comments to make Doxygen happy.
#
# $Id: __doc__.py 3902 2011-06-27 18:31:02Z sra $
#
# Copyright (C) 2009--2010  Internet Systems Consortium ("ISC")
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND ISC DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS.  IN NO EVENT SHALL ISC BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
# OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.
#
# Portions copyright (C) 2007--2008  American Registry for Internet Numbers ("ARIN")
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND ARIN DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS.  IN NO EVENT SHALL ARIN BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
# OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

## @mainpage RPKI Engine Reference Manual
#
# This collection of Python modules implements a prototype of the
# RPKI Engine.  This is a work in progress.
#
# See http://subvert-rpki.hactrn.net/ for code and
# design documents.
#
# The RPKI Engine is an implementation of the production-side tools
# for generating certificates, CRLs, and ROAs.  The
# <a href="http://subvert-rpki.hactrn.net/rcynic/">relying party tools</a>
# are a separate (and much simpler) package.
#
# The Subversion repository for the entire project is available for
# (read-only) anonymous access at http://subvert-rpki.hactrn.net/.
#
# The documentation you're reading is generated automatically by
# Doxygen from comments and documentation in
# <a href="http://subvert-rpki.hactrn.net/rpkid/rpki/">the code</a>.
#
# Besides the automatically-generated code documentation, this manual
# also includes documentation of the overall package:
#
# @li @subpage Overview "Overview of the tools"
#
# @li @subpage Installation "Installation instructions"
#
# @li @subpage Configuration "Configuration instructions"
#
# @li @subpage MySQL-Setup "MySQL setup instructions"
#
# @li The @subpage myrpki "myrpki tool"
#
# @li A description of the @subpage Left-Right "left-right protocol"
#
# @li A description of the @subpage Publication "publication protocol"
#
# @li A description of the @subpage bpki-model "BPKI model"
#     used to secure the up-down, left-right, and %publication protocols
#
# @li A description of the several @subpage sql-schemas "SQL database schemas"
#
# This work was funded from 2006 through 2008 by <a
# href="http://www.arin.net/">ARIN</a>, in collaboration with the
# other Regional Internet Registries.  Current work is funded by DHS.

## @page Overview Overview
#
# @section Terminology Terminology
#
# A few special terms that appear often enough in code or
# documentation that they need explaining.
#
# @todo
# These explanations should be fleshed out properly.
#
# @par IRBE:
#       Internet Registry Back End.
#
# @par IRDB:
#       Internet Registry Data Base.
#
# @par BPKI:
#       Business PKI.
#
# @par RPKI:
#       Resource PKI.
#
#
# @section Programs Programs
#
# At present the package is intended to be run out of the @c rpkid/
# directory.
#
# In addition to the library routines in the @c rpkid/rpki/ directory,
# the package includes the following programs:
#
# @li @ref rpkid "@c rpkid":
#              The main RPKI engine daemon.
#
# @li @ref pubd "@c pubd":
#              The publication engine daemon.
#
# @li @ref rootd "@c rootd"
#              A separate daemon for handling the root of an RPKI
#              certificate tree.  This is essentially a stripped down
#              version of rpkid with no SQL database, no left-right
#              protocol implementation, and only the parent side of
#              the up-down protocol.  It's separate because the root
#              is a special case in several ways and it was simpler
#              to keep the special cases out of the main daemon.
#
# @li @ref irdbd "@c irdbd":
#              A sample implementation of an IR database daemon.
#              rpkid calls into this to perform lookups via the
#              left-right protocol.
#
# @li @ref smoketest "@c smoketest":
#              A test tool for running a collection of rpkid and irdb
#              instances under common control, driven by a unified
#              test script.
#
# @li @ref yamltest "@c yamltest":
#              Another test tool which takes the same input format as
#              @c smoketest.py, but with slightly different purpose.
#              @c smoketest.py is intended to support regression tests,
#              while @c yamltest.py is intended for automated testing
#              of something closer to a real operational environment.
#              There's a fair amount of code duplication between the
#              two, and at some point they will probably be merged
#              into a single program that supports both modes of
#              operation.
#
# Most of these programs take configuration files in a common format
# similar to that used by the OpenSSL command line tool.  The test
# programs also take input in YAML format to drive the tests.  Runs of
# the @c yamltest test tool will generate a fairly complete set
# configuration files which may be useful as examples.
#
# Basic operation consists of creating the appropriate MySQL databases
# (see @ref MySQL-Setup "MySQL Setup"), configuring relationships
# between parents and children and between publication clients and
# repositories (see @ref MyRPKI "The myrpki tool"), starting @c rpkid,
# @c pubd, @c rootd, and @c irdbd, and using the left-right and
# publication control protocols (see @ref MyRPKI "The myrpki tool") to
# set up rpkid's and pubd's internal state.  All other operations
# should occur either as a result of cron events or as a result of
# incoming left-right and up-down protocol requests.
#
# The core programs are all event-driven, and are (in theory) capable
# of supporting an arbitrary number of hosted RPKI engines to run in a
# single rpkid instance, up to the performance limits of the underlying
# hardware.
#
# At present the daemon programs all run in foreground, that is, the
# daemons themselves make no attempt to put themselves in background.
# The easiest way to run the servers is to run the @c start_servers
# script, which examines your @c rpki.conf file and starts the
# appropriate servers in background using @c rpki.conf as the
# configuration file for each server as well.
#
# If you prefer, you can run each server by hand instead of using the
# script, eg, using Bourne shell syntax to run rpkid in background:
#
# @verbatim
#   $ rpkid &
#   $ echo >rpkid.pid  "$!"
# @endverbatim
#
# All of the daemons use syslog by default.  You can change this by
# running either the servers themselves or the @c start_servers script
# with the "-d" option.  Used as an argument to a server directly,
# "-d" causes that server to log to @c stderr instead of to syslog.
# Used as an argument to @c start_servers, "-d" starts each of the
# servers with "-d" while redirecting @c stderr from each server to a
# separate log file.  This is intended primarily for debugging.
#
# Some of the options that the several daemons take are common to all
# daemons.  Which daemon they affect depends only on which sections of
# which config files they are in.  See
# @ref CommonOptions "Common Options"
# for details.
#
# @subsection rpkid rpkid
#
# rpkid is the main RPKI engine daemon.  Configuration of rpkid is a
# two step process: a %config file to bootstrap rpkid to the point
# where it can speak using the @ref Left-Right "left-right protocol",
# followed by dynamic configuration via the left-right protocol.  The
# latter stage is handled by the @c myrpki tool.
#
# rpkid stores dynamic data in an SQL database, which must have been
# created for it, as explained in the
# @ref Installation "Installation Guide".
#
#
# @subsection pubd pubd
#
# pubd is the publication daemon.  It implements the server side of
# the publication protocol, and is used by rpkid to publish the
# certificates and other objects that rpkid generates.
#
# pubd is separate from rpkid for two reasons:
#
# @li The hosting model allows entities which choose to run their own
#     copies of rpkid to publish their output under a common
#     publication point.  In general, encouraging shared publication
#     services where practical is a good thing for relying parties,
#     as it will speed up rcynic synchronization time.
#
# @li The publication server has to run on (or at least close to) the
#     publication point itself, which in turn must be on a publically
#     reachable server to be useful.  rpkid, on the other hand, need
#     only be reachable by the IRBE and its children in the RPKI tree.
#     rpkid is a much more complex piece of software than pubd, so in
#     some situations it might make sense to wrap tighter firewall
#     constraints around rpkid than would be practical if rpkid and
#     pubd were a single program.
#
# pubd stores dynamic data in an SQL database, which must have been
# created for it, as explained in the
# @ref Installation "Installation Guide".  pubd also
# stores the published objects themselves as disk files in a
# configurable location which should correspond to an appropriate
# module definition in rsync.conf; see the
# @ref Configuration "Configuration Guide"
# for details.
#
#
# @subsection rootd rootd
#
# rootd is a stripped down implmenetation of (only) the server side of
# the up-down protocol.  It's a separate program because the root
# certificate of an RPKI certificate tree requires special handling
# and may also require a special handling policy.  rootd is a simple
# implementation intended for test use, it's not suitable for use in a
# production system.  All configuration comes via the %config file;
# see the
# @ref Configuration "Configuration Guide"
# for details.
#
#
# @subsection irdbd irdbd
#
# irdbd is a sample implemntation of the server side of the IRDB
# callback subset of the left-right protocol.  In production use this
# service is a function of the IRBE stub; irdbd may be suitable for
# production use in simple cases, but an IR with a complex IRDB may need
# to extend or rewrite irdbd.
#
# irdbd requires a pre-populated database to represent the IR's
# customers.  irdbd expects this database to use
# @ref irdbd-sql "the SQL schema defined in rpkid/irdbd.sql".
# Once this database has been populated, the IRBE stub needs to create
# the appropriate objects in rpkid's database via the control subset
# of the left-right protocol, and store the linkage handles (foreign
# keys into rpkid's database) in the IRDB.  See the
# @ref Installation "Installation Guide"
# and the
# @ref MySQL-Setup "MySQL setup instructions"
# for details.
#
#
# @subsection smoketest smoketest
#
# smoketest is a test harness to set up and run a collection of rpkid and
# irdbd instances under scripted control.
#
# Unlike the programs described above, smoketest takes two configuration
# files in different languages.  The first configuration file uses the
# same syntax as the above configuration files but is completely
# optional.  The second configuration file is the test script, which is
# encoded using the YAML serialization language (see
# http://www.yaml.org/ for more information on YAML).  The YAML script
# is not optional, as it describes the test layout.  smoketest is designed
# to support running a fairly wide set of test configurations as canned
# scripts without writing any new control code.  The intent is to make
# it possible to write meaningful regression tests.
#
# See @ref smoketestconf "smoketest.conf" for what can go into the
# (optional) first configuration file.
#
# See @ref smoketestyaml "smoketest.yaml" for what goes into the
# (required) second configuration file.
#
#
# @subsection yamltest yamltest
#
# yamltest is another test harness to set up and run a collection of
# rpkid and irdbd instances under scripted control.  It is similar in
# many ways to @ref smoketest "@c smoketest", and in fact uses the
# same YAML test description language, but its purpose is different:
# @c smoketest runs a particular test scenario through a series of
# changes, then shuts it down; @c yamltest, on the other hand, sets up
# a test network using the same tools that a real user would
# (principally the @c myrpki tool), and leaves the test running
# indefinitely.
#
# @c yamltest grew out of @c smoketest and the two probably should be
# merged back into a single tool which supports both kinds of testing.
#
#
# @section further-reading Further Reading
#
# If you're interested in this package you might also be interested
# in:
#
# @li <a href="http://subvert-rpki.hactrn.net/rcynic/">The rcynic validation tool</a>
#
# @li <a href="http://www.hactrn.net/opaque/rcynic.html">A live sample of rcynic's summary output</a>
#
#
# @section getting-started Getting Started
#
# The first step to bringing up rpkid and friends is installing the code,
# which is described in the @ref Installation "Installation Guide".

## @page Installation Installation Guide
#
# Installation instructions for rpkid et al.  These are the
# production-side RPKI tools, for Internet Registries (RIRs, LIRs,
# etc).  See the "rcynic" program for relying party tools.
#
# rpkid is a set of Python modules supporting generation and maintenance
# of resource certificates.  Most of the code is in the rpkid/rpki/
# directory.  rpkid itself is a relatively small program that calls the
# library modules.  There are several other programs that make use of
# the same libraries, as well as a collection of test programs.
#
# At present the package is intended to be run out of its build
# directory.  Setting up proper installation in a system area using the
# Python distutils package would likely not be very hard but has not yet
# been done.
#
# Note that initial development of this code has been on FreeBSD, so
# installation will probably be easiest on FreeBSD.
#
# Before attempting to build the package, you need to install any
# missing prerequisites.  Note that the Python code requires Python
# version 2.5 or 2.6.  rpkid et al are mostly self-contained, but do
# require a small number of external packages to run.
#
# <ul>
#   <li>
#     If your Python installation does not already include the sources
#     files needed to compile new Python extension modules, you will
#     need to install whatever package does include those source
#     files.  The need for and name of this package varies from system
#     to system.  On FreeBSD, the base Python interpreter package
#     includes the development sources; on at least some Linux
#     distributions, you have to install a separate "python-devel"
#     package or something similar.  If you get compilation errors
#     trying to build the POW code (below) and the error message says
#     something about the file "Python.h" being missing, this is
#     almost certainly your problem.
#   </li>
#
#   <li>
#     <a href="http://codespeak.net/lxml/">http://codespeak.net/lxml/</a>,
#     a Pythonic interface to the Gnome LibXML2 libraries.  
#     lxml in turn requires the LibXML2 C libraries.
#     <ul>
#       <li>FreeBSD: /usr/ports/devel/py-lxml</li>
#       <li>Fedora:  python-lxml.i386</li>
#       <li>Ubuntu:  python-lxml</li>
#     </ul>
#   </li>
#
#   <li>
#     <a href="http://sourceforge.net/projects/mysql-python/">http://sourceforge.net/projects/mysql-python/</a>,
#     the Python "db" interface to MySQL.  MySQLdb in turn requires MySQL client and server.  rpkid et al have
#     been tested with MySQL 5.0 and 5.1.
#     <ul>
#       <li>FreeBSD: /usr/ports/databases/py-MySQLdb</li>
#       <li>Fedora:  MySQL-python.i386</li>
#       <li>Ubuntu:  python-mysqldb</li>
#     </ul>
#   </li>
# </ul>
#
# rpkid et al also make heavy use of a modified copy of the Python
# OpenSSL Wrappers (POW) package, but this copy has enough modifications
# and additions that it's included in the subversion tree.
#
# The next step is to build the OpenSSL and POW binaries.  At present
# the OpenSSL code is just a snapshot of the OpenSSL development
# sources, compiled with special options to enable RFC 3779 support
# that ISC wrote under previous contract to ARIN.  The POW (Python
# OpenSSL Wrapper) library is an extended copy of the stock POW
# release.
#
# To build these, cd to the top-level directory in the distribution,
# run the configure script, then run "make":
#
# @verbatim
#   $ cd $top
#   $ ./configure
#   $ make
# @endverbatim
#
# This should automatically build everything, in the right order,
# including linking the POW extension module with the OpenSSL library
# to provide RFC 3779 support.  If you get errors building POW, see
# the above discussion of Python development sources.
#
# The architecture is intended to support hardware signing modules
# (HSMs), but the code to support them has not been written.
#
# At this point, you should have all the necessary software installed
# to run the core programs, but you will probably want to test it.
# The test suite requires a few more external packages, only one of
# which is Python code.
#
# <ul>
#   <li>
#     <a href="http://pyyaml.org/">http://pyyaml.org/</a>.
#     Several of the test programs use PyYAML to parse a YAML
#     description of a simulated allocation hierarchy to test.
#     <ul>
#       <li>FreeBSD: /usr/ports/devel/py-yaml</li>
#       <li>Ubuntu: python-yaml</li>
#     </ul>
#   </li>
#
#   <li>
#     <a href="http://xmlsoft.org/XSLT/">http://xmlsoft.org/XSLT/</a>.
#     Some of the test code uses xsltproc, from the Gnome LibXSLT
#     package.
#     <ul>
#       <li>FreeBSD: /usr/ports/textproc/libxslt</li>
#       <li>Ubuntu:  xsltproc</li>
#     </ul>
#   </li>
# </ul>
#
# All tests should be run from the rpkid/ directories.  
#
# Some of the tests require MySQL databases to store their data.  To
# set up all the databases that the tests will need, run the SQL
# commands in rpkid/tests/smoketest.setup.sql.  The MySQL command line
# client is usually the easiest way to do this, eg:
#
# @verbatim
#   $ cd $top/rpkid
#   $ mysql -u root -p <tests/smoketest.setup.sql
# @endverbatim
#
# To run the tests, run "make all-tests":
#
# @verbatim
#   $ cd $top/rpkid
#   $ make all-tests
# @endverbatim
#
# If nothing explodes, your installation is probably ok.  Any Python
# backtraces in the output indicate a problem.
#
# There's a last set of tools that only developers should need, as
# they're only used when modifying schemas or regenerating the
# documentation.  These tools are listed here for completeness.
#
# <ul>
#   <li>
#     <a href="http://www.doxygen.org/">http://www.doxygen.org/</a>.
#     Doxygen in turn pulls in several other tools, notably Graphviz,
#     pdfLaTeX, and Ghostscript.
#     <ul>
#       <li>FreeBSD: /usr/ports/devel/doxygen</li>
#       <li>Ubuntu: doxygen</li>
#     </ul>
#   </li>
#
#   <li>
#     <a href="http://www.mbayer.de/html2text/">http://www.mbayer.de/html2text/</a>.
#     The documentation build process uses xsltproc and html2text to dump
#     flat text versions of a few critical documentation pages.
#     <ul>
#       <li>FreeBSD: /usr/ports/textproc/html2text</li>
#     </ul>
#   </li>
#
#   <li>
#     <a href="http://www.thaiopensource.com/relaxng/trang.html">http://www.thaiopensource.com/relaxng/trang.html</a>.
#     Trang is used to convert RelaxNG schemas from the human-readable
#     "compact" form to the XML form that LibXML2 understands.  Trang in
#     turn requires Java.
#     <ul>
#       <li>FreeBSD: /usr/ports/textproc/trang</li>
#     </ul>
#   </li>
#
#   <li>
#     <a href="http://search.cpan.org/dist/SQL-Translator/">http://search.cpan.org/dist/SQL-Translator/</a>.
#     SQL-Translator, also known as "SQL Fairy", includes code to parse
#     an SQL schema and dump a description of it as Graphviz input.
#     SQL Fairy in turn requires Perl.
#     <ul>
#       <li>FreeBSD: /usr/ports/databases/p5-SQL-Translator</li>
#     </ul>
#   </li>
# </ul>
#
# Once you've finished with installation, the next thing you should
# read is the @ref Configuration "Configuration Guide".

## @page Configuration Configuration Guide
#
# This section describes the configuration file syntax and settings.
#
# Each of the programs that make up the RPKI tookit can potentially
# take its own configuration file, but for most uses this is
# unnecessarily complicated.  The recommended approach is to use a
# single configuration file, and to put all of the parameters that a
# normal user might need to change into a single section of that
# configuration file, then reference these common settings from the
# program-specific sections of the configuration file via macro
# expansion.  The configuration file parser supports a limited version
# of the macro facility used in OpenSSL's configuration parser.  An
# expression such as @verbatim foo = ${bar::baz} @endverbatim sets foo
# to the value of the @c baz variable from section @c bar.  The section
# name @c ENV is special: it refers to environment variables.
#
# @section rpkiconf rpki.conf
#
# The default name for the shared configuration file is @c rpki.conf.
# Unless you really know what you're doing, you should start by
# copying the @c rpki.conf from the @c rpkid/examples directory and
# modifying it, as the sample configuration file already includes all
# the additional settings necessary to use the simplified configuration.
#
# @dontinclude rpki.conf
# @skipline [myrpki]
#
# The @c [myrpki] section of @c rpki.conf contains all the
# parameters that you really need to configure.
#
# @skip #
# @until =
#
# Every resource-holding or server-operating entity needs a "handle",
# which is just an identifier by which the entity calls itself.
# Handles do not need to be globally unique, but should be chosen with
# an eye towards debugging operational problems: it's best if you use
# a handle that your parents and children will recognize as being you.
#
# @skip #
# @until bpki/servers
#
# The myrpki tool requires filenames for several input data files, the
# "business PKI" databases used to secure CMS and TLS communications,
# and the XML intermediate format that it uses.  Rather than
# hardwiring the names into the code, they're configured here.  You
# can change the names if you must, but the defaults should be fine in
# most cases.
#
# @skip #
# @until irdbd_server_port
#
# If you're hosting RPKI service for others, or are self-hosting, you
# want this on.  If somebody else is running rpkid on your behalf and
# you're just shipping them your @c myrpki.xml file, you can turn this
# off.
#
# If you're running @c rpkid at all, you'll need to set at least the
# @c rpkid_server_host parameter here.  You may be able to use the
# default port numbers, or may need to pick different ones.  Unless
# you plan to run @c irdbd on a different machine from @c rpkid, you
# should leave @c irdbd_server_host alone.
#
# @skip #
# @until pubd_contact_info
#
# The myrpki tool will attempt to negotiate publication service for
# you with whatever publication service your parent is using, if you
# let it, so in most cases you should not need to run @c pubd unless
# you need to issue certificates for private IP address space or
# private Autononmous System Numbers.
#
# If you do run @c pubd, you will need to set @c pubd_server_host.
# You may also need to set @c pubd_server_port, and you should provide
# something helpful as contact information in @c pubd_contact_info if
# you plan to offer publication service to your RPKI children, so that
# grandchildren (or descendents even further down the tree) who
# receive referrals to your service will know how to contact you.
#
# @skip #
# @until rootd_server_port
#
# You shouldn't run rootd unless you're the root of an RPKI tree.  Who
# gets to be the root of the public RPKI tree is a political issue
# outside the scope of this document.  For everybody else, the only
# reason for running @c rootd (other than test purposes) would be to
# support certification of private IP addresses and ASNs.  The core
# tools can do this without any problem, but the simplified
# configuration mechanism does not (yet) make this easy to do.
#
# @skip #
# @until publication_rsync_server
#
# These parameters control the mapping between the rsync URIs
# presented by @c rsyncd and the local filesystem on the machine where
# @c pubd and @c rsyncd run.  Any changes here must also be reflected
# as changes in @c rsyncd.conf.  In most cases you should not change
# the value of @c publication_rsync_module from the default; since
# pubd can't (and should not) rewrite @c rsyncd.conf, it's best to use
# a static rsync module name here and let @c pubd do its work
# underneath that name.  In most cases @c publication_rsync_server
# should be the same as @c publication_rsync_server, which is what the
# macro invocation in the default setting does.  @c
# publication_base_directory, like other pathnames in @c rpki.conf,
# can be either a relative or absolute pathname; if relative, it's
# interpreted with respect to the directory in which the programs in
# question were started.  In this specific case, it's probably better
# to use an absolute pathname, since this pathname must also appear in
# @c rsyncd.conf.
#
# @skip #
# @until pubd_sql_password
#
# These settings control how @c rpkid, @c irdbd, and @c pubd talk to
# the MySQL server.  At minimum, each daemon needs its own database;
# in the simplest configuration, the username and password can be
# shared, which is what the macro references in the default
# configuration does.  If for some reason you need to set different
# usernames and passwords for different daemons, you can do so by
# changing the daemon-specific variables.
#
# @skip #
# @until = openssl
#
# The @c myrpki tool uses the @c openssl command line tool for most of
# its BPKI operations, for two reasons:
#
# @li To avoid duplicating CA-management functionality already
# provided by the command line tool, and
#
# @li To ease portability of the @c myrpki tool, so that a "hosted"
# resource holder can use it without needing to install entire toolkit.
#
# The @c myrpki tool's use of OpenSSL does not require exotic features
# like RFC 3779 support, but it does require a version of the tool
# recent enough to support CMS and the @c -ss_cert argument to the @c
# ca command.  Depending on the platform on which you are running this
# code, you may or may not have a system copy of the @c openssl tool
# installed that meets these criteria; if not, the @c openssl binary
# built when you compile the toolkit will suffice.  This parameter
# allows you to tell @c myrpki where to find the binary, if necessary;
# the default just uses the system search path.
#
# @section otherconf Other configuration files and options
#
# In most cases the simplified configuration in the @c [myrpki]
# section of @c rpki.conf should suffice, but in case you need to
# tinker, here are details on the the rest of the configuration
# options.  In most cases the default name of the configuration file
# for a program is the name of the program followed by @c ".conf", and
# the section name is also named for the program, so that you can
# combine sections into a single configuration file as shown with @c
# rpki.conf.
#
# @li @subpage CommonOptions "Common configuration options"
#
# @li @subpage rpkidconf "rpkid configuration"
#
# @li @subpage irdbdconf "irdbd configuration"
#
# @li @subpage pubdconf  "pubd configuration"
#
# @li @subpage rootdconf "rootd configuration"
#
# @li @subpage smoketestconf "configuration of the smoketest test harness"
#
# @li @subpage smoketestyaml "test description language for the smoketest test harness"
#
# Once you've finished with configuration, the next thing you should
# read is the @ref MySQL-Setup "MySQL setup instructions".
 
## @page MySQL-Setup MySQL Setup
#
# You need to install MySQL and set up the relevant databases before
# starting @c rpkid, @c irdbd, or @c pubd.
#
# See the @ref Installation "Installation Guide" for details on where
# to download MySQL and find documentation on installing it.
#
# See the @ref Configuration "Configuration Guide" for details on the
# configuration file settings the daemons will use to find and
# authenticate themselves to their respective databases.
#
# Before you can (usefully) start any of the daemons, you will need to
# set up the MySQL databases they use.  You can do this by hand, or
# you can use the @c rpki-sql-setup script, which prompts you for your
# MySQL root password then attempts to do everything else
# automatically using values from rpki.conf.
#
# Using the script is simple:
#
# @verbatim
# $ rpki-sql-setup.py
# Please enter your MySQL root password:
# @endverbatim
#
# The script should tell you what databases it creates.  You can use
# the -v option if you want to see more details about what it's doing.
#
# If you'd prefer to do the SQL setup manually, perhaps because you
# have valuable data in other MySQL databases and you don't want to
# trust some random setup script with your MySQL root password, you'll
# need to use the MySQL command line tool, as follows:
#
# @verbatim
# $ mysql -u root -p
# 
# mysql> CREATE DATABASE irdb_database;
# mysql> GRANT all ON irdb_database.* TO irdb_user@localhost IDENTIFIED BY 'irdb_password';
# mysql> USE irdb_database;
# mysql> SOURCE $top/rpkid/irdbd.sql;
# mysql> CREATE DATABASE rpki_database;
# mysql> GRANT all ON rpki_database.* TO rpki_user@localhost IDENTIFIED BY 'rpki_password';
# mysql> USE rpki_database;
# mysql> SOURCE $top/rpkid/rpkid.sql;
# mysql> COMMIT;
# mysql> quit
# @endverbatim
#
# where @c irdb_database, @c irdb_user, @c irdb_password, @c
# rpki_database, @c rpki_user, and @c rpki_password match the values
# you used in your configuration file.
#
# If you are running pubd and are doing manual SQL setup, you'll also
# have to do:
#
# @verbatim
# $ mysql -u root -p
# mysql> CREATE DATABASE pubd_database;
# mysql> GRANT all ON pubd_database.* TO pubd_user@localhost IDENTIFIED BY 'pubd_password';
# mysql> USE pubd_database;
# mysql> SOURCE $top/rpkid/pubd.sql;
# mysql> COMMIT;
# mysql> quit
# @endverbatim
#
# where @c pubd_database, @c pubd_user @c pubd_password match the
# values you used in your configuration file.
#
# Once you've finished configuring MySQL, the next thing you should
# read is the instructions for the @ref MyRPKI "myrpki tool".


## @page MyRPKI The myrpki tool
#
# The design of rpkid and friends assumes that certain tasks can be
# thrown over the wall to the registry's back end operation.  This was
# a deliberate design decision to allow rpkid et al to remain
# independent of existing database schema, business PKIs, and so forth
# that a registry might already have.  All very nice, but it leaves
# someone who just wants to test the tools or who has no existing back
# end with a fairly large programming project.  The @c myrpki tool
# attempts to fill that gap.
# 
# @c myrpki is a basic implementation of what a registry back end
# would need to use rpkid and friends.  @c myrpki does not use every
# available option in the other programs, nor is it necessarily as
# efficient as possible.  Large registries will almost certainly want
# to roll their own tools, perhaps using these as a starting point.
# Nevertheless, we hope that @c myrpki will at least provide a useful
# example, and may be adaquate for simple use.
# 
# @c myrpki is (currently) implemented as a single command line Python
# program.  It has a number of commands, most of which are used for
# initial setup, some of which are used on an ongoing basis.  @c
# myrpki can be run either in an interactive mode or by passing a
# single command on the command line when starting the program; the
# former mode is intended to be somewhat human-friendly, the latter
# mode is useful in scripting, cron jobs, and automated testing.
# 
# @c myrpki use has two distinct phases: setup and data maintenance.
# The setup phase is primarily about constructing the "business PKI"
# (BPKI) certificates that the daemons use to authenticate CMS
# messages and obtaining the service URLs needed to configure
# the daemons.  The data maintenance phase is about configuring local
# data into the daemons.
# 
# @c myrpki uses the OpenSSL command line tool for almost all
# operations on keys and certificates; the one exception to this is
# the comamnd which talks directly to the daemons, as this command
# uses the same communication libraries as the daemons themselves do.
# The intent behind using the OpenSSL command line tool for everything
# else is to allow all the other commands to be run without requiring
# all the auxiliary packages upon which the daemons depend; this can
# be useful, eg, if one wants to run the back-end on a laptop while
# running the daemons on a server, in which case one might prefer not
# to have to install a bunch of unnecessary packages on the laptop.
# 
# During setup phase @c myrpki generates and processes small XML
# messages which it expects the user to ship to and from its parents,
# children, etc via some out-of-band means (email, perhaps with PGP
# signatures, USB stick, we really don't care).  During data
# maintenance phase, @c myrpki does something similar with another XML
# file, to allow hosting of RPKI services; in the degenerate case
# where an entity is just self-hosting (ie, is running the daemons for
# itself, and only for itself), this latter XML file need not be sent
# anywhere.
# 
# The basic idea here is that a user who has resources maintains a set
# of .csv files containing a text representation of the data needed by
# the back-end, along with a configuration file containing other
# parameters.  The intent is that these be very simple files that are
# easy to generate either by hand or as a dump from relational
# database, spreadsheet, awk script, whatever works in your
# environment.  Given these files, the user then runs @c myrpki to
# extract the relevant information and encode everything about its
# back end state into an XML file, which can then be shipped to the
# appropriate other party.
# 
# Many of the @c myrpki commands which process XML input write out a
# new XML file, either in place or as an entirely new file; in
# general, these files need to be sent back to the party that sent the
# original file.  Think of all this as a very slow packet-based
# communication channel, where each XML file is a single packet.  In
# setup phase, there's generally a single round-trip per setup
# conversation; in the data maintenance phase, the same XML file keeps
# bouncing back and forth between hosted entity and hosting entity.
# 
# Note that, as certificates and CRLs have expiration and nextUpdate
# values, a low-level cycle of updates passing between resource holder
# and rpkid operator will be necessary as a part of steady state
# operation.  [The current version of these tools does not yet
# regenerate these expiring objects, but fixing this will be a
# relatively minor matter.]
# 
# The third important kind of file in this system is the
# @ref Configuration "configuration file"
# for @c myrpki.  This contains a number of sections, some of which
# are for myrpki, others of which are for the OpenSSL command line
# tool, still others of which are for the various RPKI daemon
# programs.  The examples/ subdirectory contains a commented version
# of the configuration file that explains the various parameters.
# 
# The .csv files read by myrpki are (now) misnamed: formerly, they
# used the "excel-tab" format from the Python csv library, but early
# users kept trying to make the colums line up, which didn't do what
# the users expected.  So now these files are just
# whitespace-delimted, such as a program like "awk" would understand.
# 
# Keep reading, and don't panic.
# 
# The default configuration file name for @c myrpki is
# @ref Configuration "@c rpki.conf".
# You can change this using the "-c" option when invoking myrpki, or
# by setting the environment variable MYRPKI_CONF.
# 
# See examples/*.csv for commented examples of the several CSV files.
# Note that the comments themselves are not legal CSV, they're just
# present to make it easier to understand the examples.
# 
# @section myrpkioverview  myrpki overview
# 
# Which process you need to follow depends on whether you are running
# rpkid yourself or will be hosted by somebody else.  We call the first
# case "self-hosted", because the software treats running rpkid to
# handle resources that you yourself hold as if you are an rpkid
# operator who is hosting an entity that happens to be yourself.
# 
# "$top" in the following refers to wherever you put the
# subvert-rpki.hactrn.net code.  Once we have autoconf and "make
# install" targets, this will be some system directory or another; for
# now, it's wherever you checked out a copy of the code from the
# subversion repository or unpacked a tarball of the code.
# 
# Most of the setup process looks the same for any resource holder,
# regardless of whether they are self-hosting or not.  The differences
# come in the data maintenence phase.
# 
# The steps needed during setup phase are:
# 
# @li Write a configuration file (copy $top/rpkid/examples/rpki.conf
#     and edit as needed).  You need to configure the @c [myrpki] section;
#     in theory, the rest of the file should be ok as it is, at least for
#     simple use.  You also need to create (either by hand or by dumping
#     from a database, spreadsheet, whatever) the CSV files describing
#     prefixes and ASNs you want to allocate to your children and ROAs
#     you want created.
# 
# @li Initialization ("initialize" command).  This creates the local BPKI
#     and other data structures that can be constructed just based on
#     local data such as the config file.  Other than some internal data
#     structures, the main output of this step is the "identity.xml" file,
#     which is used as input to later stages.
# 
#     In theory it should be safe to run the "initialize" command more
#     than once, in practice this has not (yet) been tested.
# 
# @li Send (email, USB stick, carrier pigeon) identity.xml to each of your
#     parents.  This tells each of your parents what you call yourself,
#     and supplies each parent with a trust anchor for your
#     resource-holding BPKI.
# 
# @li Each of your parents runs the "configure_child" command, giving
#     the identity.xml you supplied as input.  This registers your
#     data with the parent, including BPKI cross-registration, and
#     generates a return message containing your parent's BPKI trust
#     anchors, a service URL for contacting your parent via the
#     "up-down" protocol, and (usually) either an offer of publication
#     service (if your parent operates a repository) or a referral
#     from your parent to whatever publication service your parent
#     does use.  Referrals include a CMS-signed authorization token
#     that the repository operator can use to determine that your
#     parent has given you permission to home underneath your parent
#     in the publication tree.
# 
# @li Each of your parents sends (...) back the response XML file
#     generated by the "configure_child" command.
# 
# @li You feed the response message you just got into myrpki using the
#     "configure_parent" command.  This registers the parent's
#     information in your database, including BPKI
#     cross-certification, and processes the repository offer or
#     referral to generate a publication request message.
# 
# @li You send (...) the publication request message to the
#     repository.  The @c contact_info element in the request message
#     should (in theory) provide some clue as to where you should send
#     this.
# 
# @li The repository operator processes your request using myrpki's
#     "configure_publication_client" command.  This registers your
#     information, including BPKI cross-certification, and generates a
#     response message containing the repository's BPKI trust anchor
#     and service URL.
# 
# @li Repository operator sends (...) the publication confirmation message
#     back to you.
# 
# @li You process the publication confirmation message using myrpki's
#     "configure_repository" command.
# 
# At this point you should, in theory, have established relationships,
# exchanged trust anchors, and obtained service URLs from all of your
# parents and repositories.  The last setup step is establishing a
# relationship with your RPKI service host, if you're not self-hosted,
# but as this is really just the first message of an ongoing exchange
# with your host, it's handled by the data maintenance commands.
# 
# The two commands used in data maintenence phase are
# "configure_resources" and "configure_daemons".  The first is used by
# the resource holder, the second is used by the host.  In the
# self-hosted case, it is not necessary to run "configure_resources" at
# all, myrpki will run it for you automatically.
# 
# @section myrpkihosted Hosted case
# 
# The basic steps involved in getting started for a resource holder who
# is being hosted by somebody else are:
# 
# @li Run through steps listed in
#     @ref myrpkioverview "the myrpki overview section".
# 
# @li Run the configure_resources command to generate myrpki.xml.
# 
# @li Send myrpki.xml to the rpkid operator who will be hosting you.
# 
# @li Wait for your rpkid operator to ship you back an updated XML
#     file containing a PKCS #10 certificate request for the BPKI
#     signing context (BSC) created by rpkid.
# 
# @li Run configure_resources again with the XML file you just
#     received, to issue the BSC certificate and update the XML file
#     again to contain the newly issued BSC certificate.
# 
# @li Send the updated XML file back to your rpkid operator.
# 
# At this point you're done with initial setup.  You will need to run
# configure_resources again whenever you make any changes to your
# configuration file or CSV files.
#
# @warning Once myrpki knows how to update
# BPKI CRLs, you will also need to run configure_resources periodically
# to keep your BPKI CRLs up to date.
#
# Any time you run configure_resources myrpki, you should send the
# updated XML file to your rpkid operator, who should send you a
# further updated XML file in response.
# 
# @section myrpkiselfhosted Self-hosted case
# 
# The first few steps involved in getting started for a self-hosted
# resource holder (that is, a resource holder that runs its own copy
# of rpkid) are the same as in the @ref myrpkihosted "hosted case"
# above; after that the process diverges.
# 
# The [current] steps are:
# 
# @li Follow the basic installation instructions in
#     @ref Installation "the Installation Guide" to build the
#     RFC-3779-aware OpenSSL code and associated Python extension
#     module.
# 
# @li Run through steps listed in
#     @ref myrpkioverview "the myrpki overview section".
# 
# @li Set up the MySQL databases that rpkid et al will use.  The
#     package includes a tool to do this for you, you can use that or
#     do the job by hand.  See
#     @ref MySQL-Setup "MySQL database setup"
#     for details.
# 
# @li If you are running your own publication repository (that is, if
#     you are running pubd), you will also need to set up an rsyncd
#     server or configure your existing one to serve pubd's output.
#     There's a sample configuration file in
#     $top/rpkid/examples/rsyncd.conf, but you may need to do
#     something more complicated if you are already running rsyncd for
#     other purposes.  See the rsync(1) and rsyncd.conf(5) manual
#     pages for more details.
# 
# @li Start the daemons.  You can use $top/rpkid/rpki-start-servers.py to
#     do this, or write your own script.  If you intend to run pubd,
#     you should make sure that the directory you specified as
#     publication_base_directory exists and is writable by the userid
#     that will be running pubd, and should also make sure to start
#     rsyncd.
# 
# @li Run myrpki's configure_daemons command, twice, with no
#     arguments.  You need to run the command twice because myrpki has
#     to ask rpkid to create a keypair and generate a certification
#     request for the BSC.  The first pass does this, the second
#     processes the certification request, issues the BSC, and loads
#     the result into rpkid.  [Yes, we could automate this somehow, if
#     necessary.]
# 
# At this point, if everything went well, rpkid should be up,
# configured, and starting to obtain resource certificates from its
# parents, generate CRLs and manifests, and so forth.  At this point you
# should go figure out how to use the relying party tool, rcynic: see
# $top/rcynic/README if you haven't already done so.
# 
# If and when you change your CSV files, you should run
# configure_daemons again to feed the changes into the daemons.
# 
# @section myrpkihosting Hosting case
# 
# If you are running rpkid not just for your own resources but also to
# host other resource holders (see @ref myrpkihosted "hosted case"
# above), your setup will be almost the same as in the self-hosted
# case (see @ref myrpkiselfhosted "self-hosted case", above), with one
# procedural change: you will need to tell @c configure_daemons to
# process the XML files produced by the resource holders you are
# hosting.  You do this by specifying the names of all those XML files
# on as arguments to the @c configure_daemons command.  So, if you are
# hosting two friends, Alice and Bob, then, everywhere the
# instructions for the self-hosted case say to run @c
# configure_daemons with no arguments, you will instead run it with
# the names of Alice's and Bob's XML files as arguments.
# 
# Note that @c configure_daemons sometimes modifies these XML files,
# in which case it will write them back to the same filenames.  While
# it is possible to figure out the set of circumstances in which this
# will happen (at present, only when @c myrpki has to ask @c rpkid to
# create a new BSC keypair and PKCS #10 certificate request), it may
# be easiest just to ship back an updated copy of the XML file after
# every you run @c configure_daemons.
# 
# @section myrpkipurehosting "Pure" hosting case
# 
# In general we assume that anybody who bothers to run @c rpkid is
# also a resource holder, but the software does not insist on this.
# 
# @todo
# Er, well, rpkid doesn't, but myrpki now does -- "pure" hosting was an
# unused feature that fell by the wayside while simplifying the user
# interface.  It would be relatively straightforward to add it back if
# we ever need it for anything, but the mechanism it used to use no
# longer exists -- the old [myirbe] section of the config file has been
# collapsed into the [myrpki] section, so testing for existance of the
# [myrpki] section no longer works.  So we'll need an explicit
# configuration option, no big deal, just not worth chasing now.
# 
# A (perhaps) plausible use for this capability would be if you are an
# rpkid-running resource holder who wants for some reason to keep the
# resource-holding side of your operation completely separate from the
# rpkid-running side of your operation.  This is essentially the
# pure-hosting model, just with an internal hosted entity within a
# different part of your own organization.
# 
# @section myrpkitroubleshooting Troubleshooting
# 
# If you run into trouble setting up this package, the first thing to do
# is categorize the kind of trouble you are having.  If you've gotten
# far enough to be running the daemons, check their log files.  If
# you're seeing Python exceptions, read the error messages.  If you're
# getting TLS errors, check to make sure that you're using all the right
# BPKI certificates and service contact URLs.
# 
# TLS configuration errors are, unfortunately, notoriously difficult to
# debug, because connection failures due to misconfiguration happen
# early, deep in the guts of the OpenSSL TLS code, where there isn't
# enough application context available to provide useful error messages.
# 
# If you've completed the steps above, everything appears to have gone
# OK, but nothing seems to be happening, the first thing to do is
# check the logs to confirm that nothing is actively broken.  @c
# rpkid's log should include messages telling you when it starts and
# finishes its internal "cron" cycle.  It can take several cron cycles
# for resources to work their way down from your parent into a full
# set of certificates and ROAs, so have a little patience.  @c rpkid's
# log should also include messages showing every time it contacts its
# parent(s) or attempts to publish anything.
# 
# @c rcynic in fully verbose mode provides a fairly detailed
# explanation of what it's doing and why objects that fail have
# failed.
# 
# You can use @c rsync (sic) to examine the contents of a publication
# repository one directory at a time, without attempting validation,
# by running rsync with just the URI of the directory on its command
# line:
#
# @verbatim
#   $ rsync rsync://rpki.example.org/where/ever/
# @endverbatim
# 
# @section myrpkiknownissues Known Issues
# 
# The lxml package provides a Python interface to the Gnome libxml2
# and libxslt C libraries.  This code has been quite stable for
# several years, but initial testing with lxml compiled and linked
# against a newer version of libxml2 ran into problems (specifically,
# gratuitous RelaxNG schema validation failures).  libxml2 2.7.3
# worked; libxml2 2.7.5 did not work on the test machine in question.
# Reverting to libxml2 2.7.3 fixed the problem.  Rewriting the two
# lines of Python code that were triggering the lxml bug appears to
# have solved the problem, so the code now works properly with libxml
# 2.7.5, but if you start seeing weird XML validation failures, it
# might be another variation of this lxml bug.
# 
# An earlier version of this code ran into problems with what appears
# to be an implementation restriction in the the GNU linker ("ld") on
# 64-bit hardware, resulting in obscure build failures.  The
# workaround for this required use of shared libraries and is somewhat
# less portable than the original code, but without it the code simply
# would not build in 64-bit environments with the GNU tools.  The
# current workaround appears to behave properly, but the workaround
# requires that the pathname to the RFC-3779-aware OpenSSL shared
# libraries be built into the _POW.so Python extension module.  If
# necessary, you can override this by setting the LD_LIBRARY_PATH
# environment variable, see the ld.so man page for details.  This is a
# relatively minor variation on the usual build issues for shared
# libraries, it's just annoying because shared libraries should not be
# needed here and would not be if not for this GNU linker issue.

## @page CommonOptions Common Configuration Options
#
# Some of the options that the several daemons take are common to all
# daemons.  Which daemon they affect depends only on which sections of
# which config files they are in.
#
# The first group of options are debugging flags, which can be set to
# "true" or "false".  If not specified, default values will be chosen
# (generally false).
#
# @par @c debug_http:
#                               Enable verbose http debug logging.
#
# @par @c debug_tls_certs:
#                               Enable verbose logging about tls certs.
#
# @par @c want_persistent_client:
#                               Enable http 1.1 persistence, client side.
#
# @par @c want_persistent_server:
#                               Enable http 1.1 persistence, server side.
#
# @par @c debug_cms_certs:
#                               Enable verbose logging about cms certs.
#
# @par @c sql_debug:
#                               Enable verbose logging about sql operations.
#
# @par @c gc_debug:
#                               Enable scary garbage collector debugging.
#
# @par @c timer_debug:
#                               Enable verbose logging of timer system.
#
# There are also a few options that allow you to save CMS messages for
# audit or debugging.  The save format is a simple MIME encoding in a
# Maildir-format mailbox.  The current options are very crude, at some
# point we may provide finer grain controls.
#
# @par @c dump_outbound_cms:
#                               Dump messages we send to this mailbox.
#
# @par @c dump_inbound_cms:
#                               Dump messages we receive to this mailbox.

## @page rpkidconf rpkid.conf
#
# rpkid's default %config file is rpkid.conf, start rpkid with "-c
# filename" to choose a different %config file.  All options are in
# the section "[rpkid]".  Certificates, keys, and trust anchors may be
# in either DER or PEM format.
#
# %Config file options:
#
# @par @c startup-message:
#                      String to %log on startup, useful when
#                      debugging a collection of rpkid instances at
#                      once.
#
# @par @c sql-username:
#                      Username to hand to MySQL when connecting to
#                      rpkid's database.
#
# @par @c sql-database:
#                      MySQL's database name for rpkid's database.
#
# @par @c sql-password:
#                      Password to hand to MySQL when connecting to
#                      rpkid's database.
#
# @par @c bpki-ta:
#                      Name of file containing BPKI trust anchor.
#                      All BPKI certificate verification within rpkid
#                      traces back to this trust anchor. 
#
# @par @c rpkid-cert:
#                      Name of file containing rpkid's own BPKI EE
#                      certificate.
#
# @par @c rpkid-key:
#                      Name of file containing RSA key corresponding
#                      to rpkid-cert.
#
# @par @c irbe-cert:
#                      Name of file containing BPKI certificate used
#                      by IRBE when talking to rpkid.
#
# @par @c irdb-cert:
#                      Name of file containing BPKI certificate used
#                      by irdbd.
#
# @par @c irdb-url:
#                      Service URL for irdbd.  Must be a %http:// URL.
#
# @par @c server-host:
#                      Hostname or IP address on which to listen for
#                      HTTP connections.  Current default is
#                      INADDR_ANY (IPv4 0.0.0.0); this will need to
#                      be hacked to support IPv6 for production.
#
# @par @c server-port:
#                      TCP port on which to listen for HTTP
#                      connections.

## @page pubdconf pubd.conf
#
# pubd's default %config file is pubd.conf, start pubd with "-c
# filename" to choose a different %config file.  All options are in
# the section "[pubd]".  Certifiates, keys, and trust anchors may be
# either DER or PEM format.
#
# %Config file options:
#
# @par @c sql-username:
#                      Username to hand to MySQL when connecting to
#                      pubd's database.
#
# @par @c sql-database:
#                      MySQL's database name for pubd's database.
#
# @par @c sql-password:
#                      Password to hand to MySQL when connecting to
#                      pubd's database.
#
# @par @c bpki-ta:
#                      Name of file containing master BPKI trust
#                      anchor for  pubd.  All BPKI validation in pubd
#                      traces back to this trust anchor.
#
# @par @c irbe-cert:
#                      Name of file containing BPKI certificate used
#                      by IRBE when talking to pubd.
#
# @par @c pubd-cert:
#                      Name of file containing BPKI certificate used
#                      by pubd.
#
# @par @c pubd-key:
#                      Name of file containing RSA key corresponding
#                      to @c pubd-cert.
#
# @par @c server-host:
#                      Hostname or IP address on which to listen for
#                      HTTP connections.  Current default is
#                      INADDR_ANY (IPv4 0.0.0.0); this will need to
#                      be hacked to support IPv6 for production.
#
# @par @c server-port:
#                      TCP port on which to listen for HTTP
#                      connections.
#
# @par @c publication-base:
#                      Path to base of filesystem tree where pubd
#                      should store publishable objects.  Default is
#                      "publication/".

## @page rootdconf rootd.conf
#
# rootd's default %config file is rootd.conf, start rootd with "-c
# filename" to choose a different %config file.  All options are in
# the section "[rootd]".  Certificates, keys, and trust anchors may be
# in either DER or PEM format.
#
# %Config file options:
#
# @par @c bpki-ta:
#                      Name of file containing BPKI trust anchor.  All
#                      BPKI certificate validation in rootd traces
#                      back to this trust anchor.
#
# @par @c rootd-bpki-cert:
#                      Name of file containing rootd's own BPKI
#                      certificate. 
#
# @par @c rootd-bpki-key:
#                      Name of file containing RSA key corresponding to
#                      rootd-bpki-cert.
#
# @par @c rootd-bpki-crl:
#                      Name of file containing BPKI CRL that would
#                      cover rootd-bpki-cert had it been revoked.
#
# @par @c child-bpki-cert:
#                      Name of file containing BPKI certificate for 
#                      rootd's one and only child (RPKI engine to
#                      which rootd issues an RPKI certificate).
#
# @par @c server-host:
#                      Hostname or IP address on which to listen for
#                      HTTP connections.  Default is localhost.
#
# @par @c server-port:
#                      TCP port on which to listen for HTTP
#                      connections.
#
# @par @c rpki-root-key:
#                      Name of file containing RSA key to use in
#                      signing resource certificates.
#
# @par @c rpki-root-cert:
#                      Name of file containing self-signed root
#                      resource certificate corresponding to
#                      rpki-root-key.
#
# @par @c rpki-root-dir:
#                      Name of directory where rootd should write
#                      RPKI subject certificate, manifest, and CRL.
#
# @par @c rpki-subject-cert:
#                      Name of file that rootd should use to save the
#                      one and only certificate it issues.
#                      Default is "Subroot.cer".
#
# @par @c rpki-root-crl:
#                      Name of file to which rootd should save its
#                      RPKI CRL.  Default is "Root.crl".
#
# @par @c rpki-root-manifest:
#                      Name of file to which rootd should save its
#                      RPKI manifest.  Default is "Root.mnf".
#
# @par @c rpki-subject-pkcs10:
#                      Name of file that rootd should use when saving
#                      a copy of the received PKCS #10 request for a
#                      resource certificate.  This is only used for
#                      debugging.  Default is not to save the PKCS
#                      #10 request.

## @page irdbdconf irdbd.conf
#
# irdbd's default %config file is irdbd.conf, start irdbd with "-c
# filename" to choose a different %config file.  All options are in the
# section "[irdbd]".  Certificates, keys, and trust anchors may be in
# either DER or PEM format.
#
# %Config file options:
#
# @par @c startup-message:
#                      String to %log on startup, useful when
#                      debugging a collection of irdbd instances at
#                      once.
#
# @par @c sql-username:
#                      Username to hand to MySQL when connecting to
#                      irdbd's database.
#
# @par @c sql-database:
#                      MySQL's database name for irdbd's database.
#
# @par @c sql-password:
#                      Password to hand to MySQL when connecting to
#                      irdbd's database.
#
# @par @c bpki-ta:
#                      Name of file containing BPKI trust anchor.  All
#                      BPKI certificate validation in irdbd traces
#                      back to this trust anchor.
#
# @par @c irdbd-cert:
#                      Name of file containing irdbd's own BPKI
#                      certificate. 
#
# @par @c irdbd-key:
#                      Name of file containing RSA key corresponding
#                      to irdbd-cert.
#
# @par @c rpkid-cert:
#                      Name of file containing certificate used the
#                      one and only by rpkid instance authorized to
#                      contact this irdbd instance.
#
# @par @c http-url:
#                      Service URL for irdbd.  Must be a %http:// URL.

## @page smoketestconf smoketest.conf
#
# All of the options in smoketest's (optional) configuration file are
# overrides for wired-in default values.  In almost all cases the
# defaults will suffice.  There are a ridiculous number of options,
# most of which noone will ever need, see the code for details.  The
# default name for this configuration file is smoketest.conf, run
# smoketest with "-c filename" to change it.

## @page smoketestyaml smoketest.yaml
#
# smoketest's second configuration file is named smoketest.yaml by
# default, run smoketest with "-y filename" to change it.  The YAML
# file contains multiple YAML "documents".  The first document
# describes the initial test layout and resource allocations,
# subsequent documents describe modifications to the initial
# allocations and other parameters.  Resources listed in the initial
# layout are aggregated automatically, so that a node in the resource
# hierarchy automatically receives the resources it needs to issue
# whatever its children are listed as holding.  Actions in the
# subsequent documents are modifications to the current resource set,
# modifications to validity dates or other non-resource parameters, or
# special commands like "sleep".
# 
# Here's an example of current usage:
#
# @verbatim
#     name:           Alice
#     valid_for:      2d
#     sia_base:       "rsync://alice.example/rpki/"
#     kids:
#       - name: Bob
#      kids:
#        - name: Carol
#          ipv4: 192.0.2.1-192.0.2.33
#          asn:  64533
#     ---
#     - name: Carol
#       valid_add:   10
#     ---
#     - name: Carol
#       add_as: 33
#       valid_add:   2d
#     ---
#     - name: Carol
#       valid_sub:   2d
#     ---
#     - name: Carol
#       valid_for:   10d
# @endverbatim
#
# This specifies an initial layout consisting of an RPKI engine named
# "Alice", with one child "Bob", which in turn has one child "Carol".
# Carol has a set of assigned resources, and all resources in the system
# are initially set to be valid for two days from the time at which the
# test is started.  The first subsequent document adds ten seconds to
# the validity interval for Carol's resources and makes no other
# modifications.  The second subsequent document grants Carol additional
# resources and adds another two days to the validity interval for
# Carol's resources.  The next document subtracts two days from the
# validity interval for Carol's resources.  The final document sets the
# validity interval for Carol's resources to ten days.
#
# Operators in subsequent (update) documents:
#
# @par @c add_as:
#              Add ASN resources.
#
# @par @c add_v4:
#              Add IPv4 resources.
#
# @par @c add_v6:
#              Add IPv6 resources.
#
# @par @c sub_as:
#              Subtract ASN resources.
#
# @par @c sub_v4:
#              Subtract IPv4 resources.
#
# @par @c sub_v6:
#              Subtract IPv6 resources.
#
# @par @c valid_until:
#              Set an absolute expiration date.
#
# @par @c valid_for:
#              Set a relative expiration date.
#
# @par @c valid_add:
#              Add to validity interval.
#
# @par @c valid_sub:
#              Subtract from validity interval.
#
# @par @c sleep [interval]:
#              Sleep for specified interval, or until smoketest receives a SIGALRM signal.
#
# @par @c shell cmd...:
#              Pass rest of line verbatim to /bin/sh and block until the shell returns.
#
# Absolute timestamps should be in the form shown (UTC timestamp format
# as used in XML).
#
# Intervals (@c valid_add, @c valid_sub, @c valid_for, @c sleep) are either
# integers, in which case they're interpreted as seconds, or are a
# string of the form "wD xH yM zS" where w, x, y, and z are integers and
# D, H, M, and S indicate days, hours, minutes, and seconds.  In the
# latter case all of the fields are optional, but at least one must be
# specified.  For example, "3D4H" means "three days plus four hours".


## @page Left-Right Left-Right Protocol
#
# The left-right protocol is really two separate client/server
# protocols over separate channels between the RPKI engine and the IR
# back end (IRBE).  The IRBE is the client for one of the
# subprotocols, the RPKI engine is the client for the other.
#
# @section Operations initiated by the IRBE
#
# This part of the protcol uses a kind of message-passing.  Each %object
# that the RPKI engine knows about takes five messages: "create", "set",
# "get", "list", and "destroy".  Actions which are not just data
# operations on %objects are handled via an SNMP-like mechanism, as if
# they were fields to be set.  For example, to generate a keypair one
# "sets" the "generate-keypair" field of a BSC %object, even though there
# is no such field in the %object itself as stored in SQL.  This is a bit
# of a kludge, but the reason for doing it as if these were variables
# being set is to allow composite operations such as creating a BSC,
# populating all of its data fields, and generating a keypair, all as a
# single operation.  With this model, that's trivial, otherwise it's at
# least two round trips.
#
# Fields can be set in either "create" or "set" operations, the
# difference just being whether the %object already exists.  A "get"
# operation returns all visible fields of the %object.  A "list"
# operation returns a %list containing what "get" would have returned on
# each of those %objects.
#
# Left-right protocol %objects are encoded as signed CMS messages
# containing XML as eContent and using an eContentType OID of @c id-ct-xml
# (1.2.840.113549.1.9.16.1.28).  These CMS messages are in turn passed
# as the data for HTTP POST operations, with an HTTP content type of
# "application/x-rpki" for both the POST data and the response data.
#
# All operations allow an optional "tag" attribute which can be any
# alphanumeric token.  The main purpose of the tag attribute is to allow
# batching of multiple requests into a single PDU.
#
# @subsection self_obj <self/> object
#
# A @c &lt;self/&gt; %object represents one virtual RPKI engine.  In simple cases
# where the RPKI engine operator operates the engine only on their own
# behalf, there will only be one @c &lt;self/&gt; %object, representing the engine
# operator's organization, but in environments where the engine operator
# hosts other entities, there will be one @c @c &lt;self/&gt; %object per hosted
# entity (probably including the engine operator's own organization,
# considered as a hosted customer of itself).
#
# Some of the RPKI engine's configured parameters and data are shared by
# all hosted entities, but most are tied to a specific @c &lt;self/&gt; %object.
# Data which are shared by all hosted entities are referred to as
# "per-engine" data, data which are specific to a particular @c &lt;self/&gt;
# %object are "per-self" data.
#
# Since all other RPKI engine %objects refer to a @c &lt;self/&gt; %object via a
# "self_handle" value, one must create a @c &lt;self/&gt; %object before one can
# usefully configure any other left-right protocol %objects.
#
# Every @c &lt;self/&gt; %object has a self_handle attribute, which must be specified
# for the "create", "set", "get", and "destroy" actions.
#
# Payload data which can be configured in a @c &lt;self/&gt; %object:
#
# @par @c use_hsm (attribute):
#     Whether to use a Hardware Signing Module.  At present this option
#     has no effect, as the implementation does not yet support HSMs.
#
# @par @c crl_interval (attribute):
#     Positive integer representing the planned lifetime of an RPKI CRL
#     for this @c &lt;self/&gt;, measured in seconds.
#
# @par @c regen_margin (attribute):
#     Positive integer representing how long before expiration of an
#     RPKI certificiate a new one should be generated, measured in
#     seconds.  At present this only affects the one-off EE
#     certificates associated with ROAs.  This parameter also controls
#     how long before the nextUpdate time of CRL or manifest the CRL
#     or manifest should be updated.
#
# @par @c bpki_cert (element):
#     BPKI CA certificate for this @c &lt;self/&gt;.  This is used as part of the
#     certificate chain when validating incoming TLS and CMS messages,
#     and should be the issuer of cross-certification BPKI certificates
#     used in @c &lt;repository/&gt;, @c &lt;parent/&gt;, and @c &lt;child/&gt; %objects.  If the
#     bpki_glue certificate is in use (below), the bpki_cert certificate
#     should be issued by the bpki_glue certificate; otherwise, the
#     bpki_cert certificate should be issued by the per-engine bpki_ta
#     certificate.
#
# @par @c bpki_glue (element):
#     Another BPKI CA certificate for this @c &lt;self/&gt;, usually not needed.
#     Certain pathological cross-certification cases require a
#     two-certificate chain due to issuer name conflicts.  If used, the
#     bpki_glue certificate should be the issuer of the bpki_cert
#     certificate and should be issued by the per-engine bpki_ta
#     certificate; if not needed, the bpki_glue certificate should be
#     left unset.
#
# Control attributes that can be set to "yes" to force actions:
#
# @par @c rekey:
#     Start a key rollover for every RPKI CA associated with every
#     @c &lt;parent/&gt; %object associated with this @c &lt;self/&gt; %object.  This is the
#     first phase of a key rollover operation.
#
# @par @c revoke:
#     Revoke any remaining certificates for any expired key associated
#     with any RPKI CA for any @c &lt;parent/&gt; %object associated with this
#     @c &lt;self/&gt; %object.   This is the second (cleanup) phase for a key
#     rollover operation; it's separate from the first phase to leave
#     time for new RPKI certificates to propegate and be installed.
#
# @par @c reissue:
#     Not implemented, may be removed from protocol.  Original theory
#     was that this operation would force reissuance of any %object with
#     a changed key, but as that happens automatically as part of the
#     key rollover mechanism this operation seems unnecessary.
#
# @par @c run_now:
#     Force immediate processing for all tasks associated with this
#     @c &lt;self/&gt; %object that would ordinarily be performed under cron.  Not
#     currently implemented.
#
# @par @c publish_world_now:
#     Force (re)publication of every publishable %object for this @c &lt;self/&gt;
#     %object.  Not currently implemented.   Intended to aid in recovery
#     if RPKI engine and publication engine somehow get out of sync.
#
#
# @subsection bsc_obj <bsc/> object
#
# The @c &lt;bsc/&gt; ("business signing context") %object represents all the BPKI
# data needed to sign outgoing CMS messages.  Various other
# %objects include pointers to a @c &lt;bsc/&gt; %object.  Whether a particular
# @c &lt;self/&gt; uses only one @c &lt;bsc/&gt; or multiple is a configuration decision
# based on external requirements: the RPKI engine code doesn't care, it
# just cares that, for any %object representing a relationship for which
# it must sign messages, there be a @c &lt;bsc/&gt; %object that it can use to
# produce that signature.
#
# Every @c &lt;bsc/&gt; %object has a bsc_handle, which must be specified for the
# "create", "get", "set", and "destroy" actions.  Every @c &lt;bsc/&gt; also has a self_handle
# attribute which indicates the @c &lt;self/&gt; %object with which this @c &lt;bsc/&gt;
# %object is associated.
#
# Payload data which can be configured in a @c &lt;isc/&gt; %object:
#
# @par @c signing_cert (element):
#     BPKI certificate to use when generating a signature.
#
# @par @c signing_cert_crl (element):
#     CRL which would %list signing_cert if it had been revoked.
#
# Control attributes that can be set to "yes" to force actions:
#
# @par @c generate_keypair:
#     Generate a new BPKI keypair and return a PKCS #10 certificate
#     request.  The resulting certificate, once issued, should be
#     configured as this @c &lt;bsc/&gt; %object's signing_cert.
#
# Additional attributes which may be specified when specifying
# "generate_keypair":
#
# @par @c key_type:
#     Type of BPKI keypair to generate.  "rsa" is both the default and,
#     at the moment, the only allowed value.
#
# @par @c hash_alg:
#     Cryptographic hash algorithm to use with this keypair.  "sha256"
#     is both the default and, at the moment, the only allowed value.
#
# @par @c key_length:
#     Length in bits of the keypair to be generated.  "2048" is both the
#     default and, at the moment, the only allowed value.
#
# Replies to "create" and "set" actions that specify "generate-keypair"
# include a &lt;bsc_pkcs10/> element, as do replies to "get" and "list"
# actions for a @c &lt;bsc/&gt; %object for which a "generate-keypair" command has
# been issued.  The RPKI engine stores the PKCS #10 request, which
# allows the IRBE to reuse the request if and when it needs to reissue
# the corresponding BPKI signing certificate.
#
# @subsection parent_obj <parent/> object
#
# The @c &lt;parent/&gt; %object represents the RPKI engine's view of a particular
# parent of the current @c &lt;self/&gt; %object in the up-down protocol.  Due to
# the way that the resource hierarchy works, a given @c &lt;self/&gt; may obtain
# resources from multiple parents, but it will always have at least one;
# in the case of IANA or an RIR, the parent RPKI engine may be a trivial
# stub.
#
# Every @c &lt;parent/&gt; %object has a parent_handle, which must be specified for
# the "create", "get", "set", and "destroy" actions.  Every @c &lt;parent/&gt; also has a
# self_handle attribute which indicates the @c &lt;self/&gt; %object with which this
# @c &lt;parent/&gt; %object is associated, a bsc_handle attribute indicating the @c &lt;bsc/&gt;
# %object to be used when signing messages sent to this parent, and a
# repository_handle indicating the @c &lt;repository/&gt; %object to be used when
# publishing issued by the certificate issued by this parent.
#
# Payload data which can be configured in a @c &lt;parent/&gt; %object:
#
# @par @c peer_contact_uri (attribute):
#     HTTP URI used to contact this parent.
#
# @par @c sia_base (attribute):
#     The leading portion of an rsync URI that the RPKI engine should
#     use when composing the publication URI for %objects issued by the
#     RPKI certificate issued by this parent.
#
# @par @c sender_name (attribute):
#     Sender name to use in the up-down protocol when talking to this
#     parent.  The RPKI engine doesn't really care what this value is,
#     but other implementations of the up-down protocol do care.
#
# @par @c recipient_name (attribute):
#     Recipient name to use in the up-down protocol when talking to this
#     parent.   The RPKI engine doesn't really care what this value is,
#     but other implementations of the up-down protocol do care.
#
# @par @c bpki_cms_cert (element):
#     BPKI CMS CA certificate for this @c &lt;parent/&gt;.  This is used as part
#     of the certificate chain when validating incoming CMS messages If
#     the bpki_cms_glue certificate is in use (below), the bpki_cms_cert
#     certificate should be issued by the bpki_cms_glue certificate;
#     otherwise, the bpki_cms_cert certificate should be issued by the
#     bpki_cert certificate in the @c &lt;self/&gt; %object.
#
# @par @c bpki_cms_glue (element):
#     Another BPKI CMS CA certificate for this @c &lt;parent/&gt;, usually not
#     needed.  Certain pathological cross-certification cases require a
#     two-certificate chain due to issuer name conflicts.  If used, the
#     bpki_cms_glue certificate should be the issuer of the
#     bpki_cms_cert certificate and should be issued by the bpki_cert
#     certificate in the @c &lt;self/&gt; %object; if not needed, the
#     bpki_cms_glue certificate should be left unset.
#
# Control attributes that can be set to "yes" to force actions:
#
# @par @c rekey:
#     This is like the rekey command in the @c &lt;self/&gt; %object, but limited
#     to RPKI CAs under this parent.
#
# @par @c reissue:
#     This is like the reissue command in the @c &lt;self/&gt; %object, but limited
#     to RPKI CAs under this parent.
#
# @par @c revoke:
#     This is like the revoke command in the @c &lt;self/&gt; %object, but limited
#     to RPKI CAs under this parent.
#
# @subsection child_obj <child/> object
#
# The @c &lt;child/&gt; %object represents the RPKI engine's view of particular
# child of the current @c &lt;self/&gt; in the up-down protocol.
#
# Every @c &lt;child/&gt; %object has a child_handle, which must be specified for the
# "create", "get", "set", and "destroy" actions.  Every @c &lt;child/&gt; also has a
# self_handle attribute which indicates the @c &lt;self/&gt; %object with which this
# @c &lt;child/&gt; %object is associated.
#
# Payload data which can be configured in a @c &lt;child/&gt; %object:
#
# @par @c bpki_cert (element):
#     BPKI CA certificate for this @c &lt;child/&gt;.  This is used as part of
#     the certificate chain when validating incoming TLS and CMS
#     messages.  If the bpki_glue certificate is in use (below), the
#     bpki_cert certificate should be issued by the bpki_glue
#     certificate; otherwise, the bpki_cert certificate should be issued
#     by the bpki_cert certificate in the @c &lt;self/&gt; %object.
#
# @par @c bpki_glue (element):
#     Another BPKI CA certificate for this @c &lt;child/&gt;, usually not needed.
#     Certain pathological cross-certification cases require a
#     two-certificate chain due to issuer name conflicts.  If used, the
#     bpki_glue certificate should be the issuer of the bpki_cert
#     certificate and should be issued by the bpki_cert certificate in
#     the @c &lt;self/&gt; %object; if not needed, the bpki_glue certificate
#     should be left unset.
#
# Control attributes that can be set to "yes" to force actions:
#
# @par @c reissue:
#     Not implemented, may be removed from protocol.
#
# @subsection repository_obj <repository/> object
#
# The @c &lt;repository/&gt; %object represents the RPKI engine's view of a
# particular publication repository used by the current @c &lt;self/&gt; %object.
#
# Every @c &lt;repository/&gt; %object has a repository_handle, which must be
# specified for the "create", "get", "set", and "destroy" actions.  Every
# @c &lt;repository/&gt; also has a self_handle attribute which indicates the @c &lt;self/&gt;
# %object with which this @c &lt;repository/&gt; %object is associated.
#
# Payload data which can be configured in a @c &lt;repository/&gt; %object:
#
# @par @c peer_contact_uri (attribute):
#     HTTP URI used to contact this repository.
#
# @par @c bpki_cms_cert (element):
#     BPKI CMS CA certificate for this @c &lt;repository/&gt;.  This is used as part
#     of the certificate chain when validating incoming CMS messages If
#     the bpki_cms_glue certificate is in use (below), the bpki_cms_cert
#     certificate should be issued by the bpki_cms_glue certificate;
#     otherwise, the bpki_cms_cert certificate should be issued by the
#     bpki_cert certificate in the @c &lt;self/&gt; %object.
#
# @par @c bpki_cms_glue (element):
#     Another BPKI CMS CA certificate for this @c &lt;repository/&gt;, usually not
#     needed.  Certain pathological cross-certification cases require a
#     two-certificate chain due to issuer name conflicts.  If used, the
#     bpki_cms_glue certificate should be the issuer of the
#     bpki_cms_cert certificate and should be issued by the bpki_cert
#     certificate in the @c &lt;self/&gt; %object; if not needed, the
#     bpki_cms_glue certificate should be left unset.
#
# At present there are no control attributes for @c &lt;repository/&gt; %objects.
#
# @subsection route_origin_obj <route_origin/> object
#
# This section is out-of-date. The @c &lt;route_origin/&gt; %object
# has been replaced by the @c &lt;list_roa_requests/&gt; IRDB query,
# but the documentation for that hasn't been written yet.
#
# The @c &lt;route_origin/&gt; %object is a kind of prototype for a ROA.  It
# contains all the information needed to generate a ROA once the RPKI
# engine obtains the appropriate RPKI certificates from its parent(s).
#
# Note that a @c &lt;route_origin/&gt; %object represents a ROA to be generated on
# behalf of @c &lt;self/&gt;, not on behalf of a @c &lt;child/&gt;.  Thus, a hosted entity
# that has no children but which does need to generate ROAs would be
# represented by a hosted @c &lt;self/&gt; with no @c &lt;child/&gt; %objects but one or
# more @c &lt;route_origin/&gt; %objects.   While lumping ROA generation in with
# the other RPKI engine activities may seem a little odd at first, it's
# a natural consequence of the design requirement that the RPKI daemon
# never transmit private keys across the network in any form; given this
# requirement, the RPKI engine that holds the private keys for an RPKI
# certificate must also be the engine which generates any ROAs that
# derive from that RPKI certificate.
#
# The precise content of the @c &lt;route_origin/&gt; has changed over time as
# the underlying ROA specification has changed.  The current
# implementation as of this writing matches what we expect to see in
# draft-ietf-sidr-roa-format-03, once it is issued.  In particular, note
# that the exactMatch boolean from the -02 draft has been replaced by
# the prefix and maxLength encoding used in the -03 draft.
#
# Payload data which can be configured in a @c &lt;route_origin/&gt; %object:
#
# @par @c asn (attribute):
#     Autonomous System Number (ASN) to place in the generated ROA.  A
#     single ROA can only grant authorization to a single ASN; multiple
#     ASNs require multiple ROAs, thus multiple @c &lt;route_origin/&gt; %objects.
#
# @par @c ipv4 (attribute):
#     %List of IPv4 prefix and maxLength values, see below for format.
#
# @par @c ipv6 (attribute):
#     %List of IPv6 prefix and maxLength values, see below for format.
#
# Control attributes that can be set to "yes" to force actions:
#
# @par @c suppress_publication:
#     Not implemented, may be removed from protocol.
#
# The lists of IPv4 and IPv6 prefix and maxLength values are represented
# as comma-separated text strings, with no whitespace permitted.  Each
# entry in such a string represents a single prefix/maxLength pair.
#
# ABNF for these address lists:
#
# @verbatim
#
#   <ROAIPAddress> ::= <address> "/" <prefixlen> [ "-" <max_prefixlen> ]
#                         ; Where <max_prefixlen> defaults to the same
#                         ; value as <prefixlen>.
#
#   <ROAIPAddressList> ::= <ROAIPAddress> *( "," <ROAIPAddress> )
#
# @endverbatim
#
# For example, @c "10.0.1.0/24-32,10.0.2.0/24", which is a shorthand
# form of @c "10.0.1.0/24-32,10.0.2.0/24-24".
#
# @section irdb_queries Operations initiated by the RPKI engine
#
# The left-right protocol also includes queries from the RPKI engine
# back to the IRDB.  These queries do not follow the message-passing
# pattern used in the IRBE-initiated part of the protocol.  Instead,
# there's a single query back to the IRDB, with a corresponding
# response.  The CMS encoding are the same as in the rest of
# the protocol, but the BPKI certificates will be different as the
# back-queries and responses form a separate communication channel.
#
# @subsection list_resources_msg <list_resources/> messages
#
# The @c &lt;list_resources/&gt; query and response allow the RPKI engine to ask
# the IRDB for information about resources assigned to a particular
# child.  The query must include both a @c "self_handle" attribute naming
# the @c &lt;self/&gt; that is making the request and also a @c "child_handle"
# attribute naming the child that is the subject of the query.  The
# query and response also allow an optional @c "tag" attribute of the
# same form used elsewhere in this protocol, to allow batching.
#
# A @c &lt;list_resources/&gt; response includes the following attributes, along
# with the @c tag (if specified), @c self_handle, and @c child_handle copied
# from the request:
#
# @par @c valid_until:
#     A timestamp indicating the date and time at which certificates
#     generated by the RPKI engine for these data should expire.  The
#     timestamp is expressed as an XML @c xsd:dateTime, must be
#     expressed in UTC, and must carry the "Z" suffix indicating UTC.
#
# @par @c asn:
#     A %list of autonomous sequence numbers, expressed as a
#     comma-separated sequence of decimal integers with no whitespace.
#
# @par @c ipv4:
#     A %list of IPv4 address prefixes and ranges, expressed as a
#     comma-separated %list of prefixes and ranges with no whitespace.
#     See below for format details.
#
# @par @c ipv6:
#     A %list of IPv6 address prefixes and ranges, expressed as a
#     comma-separated %list of prefixes and ranges with no whitespace.
#     See below for format details.
#
# Entries in a %list of address prefixes and ranges can be either
# prefixes, which are written in the usual address/prefixlen notation,
# or ranges, which are expressed as a pair of addresses denoting the
# beginning and end of the range, written in ascending order separated
# by a single "-" character.  This format is superficially similar to
# the format used for prefix and maxLength values in the @c &lt;route_origin/&gt;
# %object, but the semantics differ: note in particular that
# @c &lt;route_origin/&gt; %objects don't allow ranges, while @c &lt;list_resources/&gt;
# messages don't allow a maxLength specification.
#
# @section left_right_error_handling Error handling
#
# Error in this protocol are handled at two levels.
#
# Since all messages in this protocol are conveyed over HTTP
# connections, basic errors are indicated via the HTTP response code.
# 4xx and 5xx responses indicate that something bad happened.  Errors
# that make it impossible to decode a query or encode a response are
# handled in this way.
#
# Where possible, errors will result in a @c &lt;report_error/&gt; message which
# takes the place of the expected protocol response message.
# @c &lt;report_error/&gt; messages are CMS-signed XML messages like the rest of
# this protocol, and thus can be archived to provide an audit trail.
#
# @c &lt;report_error/&gt; messages only appear in replies, never in queries.
# The @c &lt;report_error/&gt; message can appear on either the "forward" (IRBE
# as client of RPKI engine) or "back" (RPKI engine as client of IRDB)
# communication channel.
#
# The @c &lt;report_error/&gt; message includes an optional @c "tag" attribute to
# assist in matching the error with a particular query when using
# batching, and also includes a @c "self_handle" attribute indicating the
# @c &lt;self/&gt; that issued the error.
#
# The error itself is conveyed in the @c error_code (attribute).  The
# value of this attribute is a token indicating the specific error that
# occurred.  At present this will be the name of a Python exception; the
# production version of this protocol will nail down the allowed error
# tokens here, probably in the RelaxNG schema.
#
# The body of the @c &lt;report_error/&gt; element itself is an optional text
# string; if present, this is debugging information.  At present this
# capabilty is not used, debugging information goes to syslog.

## @page Publication Publication protocol
#
# The %publication protocol is really two separate client/server
# protocols, between different parties.  The first is a configuration
# protocol for an IRBE to use to configure a %publication engine,
# the second is the interface by which authorized clients request
# %publication of specific objects.
#
# Much of the architecture of the %publication protocol is borrowed
# from the @ref Left-Right "left-right protocol": like the
# left-right protocol, the %publication protocol uses CMS-wrapped XML
# over HTTP with the same eContentType OID and the same HTTP
# content-type, and the overall style of the XML messages is very
# similar to the left-right protocol.  All operations allow an
# optional "tag" attribute to allow batching.
#
# The %publication engine operates a single HTTP server which serves
# both of these subprotocols.  The two subprotocols share a single
# server port, but use distinct URLs to allow demultiplexing.
#
# @section Publication-control Publication control subprotocol
#
# The control subprotocol reuses the message-passing design of the
# left-right protocol.  Configured objects support the "create", "set",
# "get", "list", and "destroy" actions, or a subset thereof when the
# full set of actions doesn't make sense.
#
# @subsection config_obj <config/> object
#
# The &lt;config/&gt; %object allows configuration of data that apply to the
# entire %publication server rather than a particular client.
#
# There is exactly one &lt;config/&gt; %object in the %publication server, and
# it only supports the "set" and "get" actions -- it cannot be created
# or destroyed.
#
# Payload data which can be configured in a &lt;config/&gt; %object:
#
# @par @c bpki_crl (element):
#     This is the BPKI CRL used by the %publication server when
#     signing the CMS wrapper on responses in the %publication
#     subprotocol.  As the CRL must be updated at regular intervals,
#     it's not practical to restart the %publication server when the
#     BPKI CRL needs to be updated.  The BPKI model doesn't require
#     use of a BPKI CRL between the IRBE and the %publication server,
#     so we can use the %publication control subprotocol to update the
#     BPKI CRL.
#
# @subsection client_obj <client/> object
#
# The &lt;client/&gt; %object represents one client authorized to use the
# %publication server.
#
# The &lt;client/&gt; %object supports the full set of "create", "set", "get",
# "list", and "destroy" actions.  Each client has a "client_handle"
# attribute, which is used in responses and must be specified in "create", "set",
# "get", or "destroy" actions.
#
# Payload data which can be configured in a &lt;client/&gt; %object:
#
# @par @c base_uri (attribute):
#     This is the base URI below which this client is allowed to publish
#     data.  The %publication server may impose additional constraints in
#     the case of a child publishing beneath its parent.
#
# @par @c bpki_cert (element):
#     BPKI CA certificate for this &lt;client/&gt;.  This is used as part of
#     the certificate chain when validating incoming TLS and CMS
#     messages.  If the bpki_glue certificate is in use (below), the
#     bpki_cert certificate should be issued by the bpki_glue
#     certificate; otherwise, the bpki_cert certificate should be issued
#     by the %publication engine's bpki_ta certificate.
#
# @par @c bpki_glue (element):
#     Another BPKI CA certificate for this &lt;client/&gt;, usually not
#     needed.  Certain pathological cross-certification cases require a
#     two-certificate chain due to issuer name conflicts.  If used, the
#     bpki_glue certificate should be the issuer of the bpki_cert
#     certificate and should be issued by the %publication engine's
#     bpki_ta certificate; if not needed, the bpki_glue certificate
#     should be left unset.
#
# @section Publication-publication Publication subprotocol
#
# The %publication subprotocol is structured somewhat differently from
# the %publication control protocol.  Objects in the %publication
# subprotocol represent objects to be published or objects to be
# withdrawn from %publication.  Each kind of %object supports two actions:
# "publish" and "withdraw".  In each case the XML element representing
# hte %object to be published or withdrawn has a "uri" attribute which
# contains the %publication URI.  For "publish" actions, the XML element
# body contains the DER %object to be published, encoded in Base64; for
# "withdraw" actions, the XML element body is empty.
#
# In theory, the detailed access control for each kind of %object might
# be different.  In practice, as of this writing, access control for all
# objects is a simple check that the client's @c "base_uri" is a leading
# substring of the %publication URI.  Details of why access control might
# need to become more complicated are discussed in a later section.
#
# @subsection certificate_obj <certificate/> object
#
# The &lt;certificate/&gt; %object represents an RPKI certificate to be
# published or withdrawn.
#
# @subsection crl_obj <crl/> object
#
# The &lt;crl/&gt; %object represents an RPKI CRL to be published or withdrawn.
#
# @subsection manifest_obj <manifest/> object
#
# The &lt;manifest/&gt; %object represents an RPKI %publication %manifest to be
# published or withdrawn.
#
# Note that part of the reason for the batching support in the
# %publication protocol is because @em every %publication or withdrawal
# action requires a new %manifest, thus every %publication or withdrawal
# action will involve at least two objects.
#
# @subsection roa_obj <roa/> object
#
# The &lt;roa/&gt; %object represents a ROA to be published or withdrawn.
#
# @section publication_error_handling Error handling
#
# Error in this protocol are handled at two levels.
#
# Since all messages in this protocol are conveyed over HTTP
# connections, basic errors are indicated via the HTTP response code.
# 4xx and 5xx responses indicate that something bad happened.  Errors
# that make it impossible to decode a query or encode a response are
# handled in this way.
#
# Where possible, errors will result in a &lt;report_error/&gt; message which
# takes the place of the expected protocol response message.
# &lt;report_error/&gt; messages are CMS-signed XML messages like the rest of
# this protocol, and thus can be archived to provide an audit trail.
#
# &lt;report_error/&gt; messages only appear in replies, never in
# queries.  The &lt;report_error/&gt; message can appear in both the
# control and publication subprotocols.
#
# The &lt;report_error/&gt; message includes an optional @c "tag" attribute to
# assist in matching the error with a particular query when using
# batching.
#
# The error itself is conveyed in the @c error_code (attribute).  The
# value of this attribute is a token indicating the specific error that
# occurred.  At present this will be the name of a Python exception; the
# production version of this protocol will nail down the allowed error
# tokens here, probably in the RelaxNG schema.
#
# The body of the &lt;report_error/&gt; element itself is an optional text
# string; if present, this is debugging information.  At present this
# capabilty is not used, debugging information goes to syslog.
#
# @section publication_access_control Additional access control considerations.
#
# As detailed above, the %publication protocol is trivially simple.  This
# glosses over two bits of potential complexity:
#
# @li In the case where parent and child are sharing a repository, we'd
#     like to nest child under parent, because testing has demonstrated
#     that even on relatively slow hardware the delays involved in
#     setting up separate rsync connections tend to dominate
#     synchronization time for relying parties.
#
# @li The repository operator might also want to do some checks to
#     assure itself that what it's about to allow the RPKI engine to
#     publish is not dangerous toxic waste.
#
# The up-down protocol includes a mechanism by which a parent can
# suggest a %publication URI to each of its children.  The children are
# not required to accept this hint, and the children must make separate
# arrangements with the repository operator (who might or might not be
# the same as the entity that hosts the children's RPKI engine
# operations) to use the suggested %publication point, but if everything
# works out, this allows children to nest cleanly under their parents
# %publication points, which helps reduce synchronization time for
# relying parties.
#
# In this case, one could argue that the %publication server is
# responsible for preventing one of its clients (the child in the above
# description) from stomping on data published by another of its clients
# (the parent in the above description).  This goes beyond the basic
# access check and requires the %publication server to determine whether
# the parent has given its consent for the child to publish under the
# parent.  Since the RPKI certificate profile requires the child's
# %publication point to be indicated in an SIA extension in a certificate
# issued by the parent to the child, the %publication engine can infer
# this permission from the parent's issuance of a certificate to the
# child.  Since, by definition, the parent also uses this %publication
# server, this is an easy check, as the %publication server should
# already have the parent's certificate available by the time it needs
# to check the child's certificate.
#
# The previous paragraph only covers a "publish" action for a
# &lt;certificate/&gt; %object.  For "publish" actions on other
# objects, the %publication server would need to trace permission back
# to the certificate issued by the parent; for "withdraw" actions,
# the %publication server would have to perform the same checks it
# would perform for a "publish" action, using the current published
# data before withdrawing it.  The latter in turn implies an ordering
# constraint on "withdraw" actions in order to preserve the data
# necessary for these access control decisions; as this may prove
# impractical, the %publication server may probably need to make
# periodic sweeps over its published data looking for orphaned
# objects, but that's probably a good idea anyway.
#
# Note that, in this %publication model, any agreement that the
# repository makes to publish the RPKI engine's output is conditional
# upon the %object to be published passing whatever access control checks
# the %publication server imposes.

## @page sql-schemas SQL database schemas
#
# @li @subpage rpkid-sql "rpkid database schema"
# @li @subpage pubd-sql  "pubd database schema"
# @li @subpage irdbd-sql "irdbd database schema"

## @page rpkid-sql rpkid SQL schema
#
# @image html  rpkid.png "Diagram of rpkid.sql"
# @image latex rpkid.eps "Diagram of rpkid.sql" height=\textheight
#
# @verbinclude rpkid.sql

## @page pubd-sql pubd SQL Schema
#
# @image html  pubd.png "Diagram of pubd.sql"
# @image latex pubd.eps "Diagram of pubd.sql" width=\textwidth
#
# @verbinclude pubd.sql

## @page irdbd-sql irdbd SQL Schema
#
# @image html  irdbd.png "Diagram of irdbd.sql"
# @image latex irdbd.eps "Diagram of irdbd.sql" width=\textwidth
#
# @verbinclude irdbd.sql

## @page bpki-model BPKI model
#
# The "business PKI" (BPKI) is the PKI used to authenticate
# communication on the up-down, left-right, and %publication protocols.
# BPKI certificates are @em not resource PKI (RPKI) certificates.  The
# BPKI is a separate PKI that represents relationships between the
# various entities involved in the production side of the RPKI system.
# In most cases the BPKI tree will follow existing business
# relationships, hence the "B" (Business) in "BPKI".
#
# Setup of the BPKI is handled by the back end; for the most part,
# rpkid and pubd just use the result.  The one place where the engines
# are directly involved in creation of new BPKI certificates is in the
# production of end-entity certificates for use by the engines.
#
# For the most part an ordinary user of this package need not worry
# about the details explained here, as the
# @ref MyRPKI "myrpki tool"
# takes care of all of this.  However, users who want to understand
# what's going on behind the scenes or who have needs too complex for
# the myrpki tool to handle might want to understand the underlying
# model.
#
# There are a few design principals that underly the chosen BPKI model:
#
# @li Each engine should rely on a single BPKI trust anchor which is
#     controlled by the back end entity that runs the engine; all
#     other trust material should be cross-certified into the engine's
#     BPKI tree.
#
# @li Private keys must never transit the network.
#
# @li Except for end entity certificates, the engine should only have
#     access to the BPKI certificates; in particular, the private key
#     for the BPKI trust anchor should not be accessible to the engine.
#
# @li The number of BPKI keys and certificates that the engine has to
#     manage should be no larger than is necessary.
#
# rpkid's hosting model adds an additional constraint: rpkid's BPKI
# trust anchor belongs to the entity operating rpkid, but the entities
# hosted by rpkid should have control of their own BPKI private keys.
# This implies the need for an additional layer of BPKI certificate
# hierarchy within rpkid.
#
# Here is a simplified picture of what the BPKI might look like for an
# rpkid operator that hosts two entities, "Alice" and "Ellen":
#
# @image html  rpkid-bpki.png
# @image latex rpkid-bpki.eps width=\textwidth
#
# Black objects belong to the hosting entity, blue objects belong to
# the hosted entities, red objects are cross-certified objects from
# the hosted entities' peers.  The arrows indicate certificate
# issuance: solid arrows are the ones that rpkid will care about
# during certificate validation, dotted arrows show the origin of the
# EE certificates that rpkid uses to sign CMS and TLS messages.
#
# The certificate tree looks complicated, but the set of certificates
# needed to build any particular validation chain is obvious.
#
# Detailed instructions on how to build a BPKI are beyond the scope of
# this document, but one can handle simple cases using the OpenSSL
# command line tool and cross_certify; the latter is a tool
# designed specifically for the purpose of generating the
# cross-certification certificates needed to splice foreign trust
# material into a BPKI tree.
#
# The BPKI tree for a pubd instance is similar to to the BPKI tree for
# an rpkid instance, but is a bit simpler, as pubd does not provide
# hosting in the same sense that rpkid does: pubd is a relatively
# simple server that publishes objects as instructed by its clients.
#
# Here's a simplified picture of what the BPKI might look like for a
# pubd operator that serves two clients, "Alice" and "Bob":
#
# @image html  pubd-bpki.png
# @image latex pubd-bpki.eps width=\textwidth
#
# While it is likely that RIRs (at least) will operate both rpkid and
# pubd instances, the two functions are conceptually separate.  As far
# as pubd is concerned, it doesn't matter who operates the rpkid
# instance: pubd just has clients, each of which has trust material
# that has been cross-certified into pubd's BPKI.  Similarly, rpkid
# doesn't really care who operates a pubd instance that it's been
# configured to use, it just treats that pubd as a foreign BPKI whose
# trust material has to be cross-certified into its own BPKI.  Cross
# certification itself is done by the back end operator, using
# cross_certify or some equivalent tool; the resulting BPKI
# certificates are configured into rpkid and pubd via the left-right
# protocol and the control subprotocol of the publication protocol,
# respectively.
#
# Because the BPKI tree is almost entirely controlled by the operating
# entity, CRLs are not necessary for most of the BPKI.  The one
# exception to this is the EE certificates issued under the
# cross-certification points.  These EE certificates are generated by
# the peer, not the local operator, and thus require CRLs.  Because of
# this, both rpkid and pubd require regular updates of certain BPKI
# CRLs, again via the left-right and publication control protocols.
#
# Because the left-right protocol and the publication control
# subprotocol are used to configure BPKI certificates and CRLs, they
# cannot themselves use certificates and CRLs configured in this way.
# This is why the configuration files for rpkid and pubd require
# static configuration of the left-right and publication control
# certificates.

# Local Variables:
# mode:python
# compile-command: "cd ../.. && ./config.status && cd rpkid && make docs"
# End:
