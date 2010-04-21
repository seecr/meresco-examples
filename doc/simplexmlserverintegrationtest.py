#!/usr/bin/env python
# encoding: utf-8
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#
#    This file is part of Meresco Components.
#
#    Meresco Components is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Components is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Components; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
import os, sys
os.system('find .. -name "*.pyc" | xargs rm -f')

from glob import glob
for path in glob('../deps.d/*'):
    sys.path.insert(0, path)

sys.path.insert(0, "..")

from os import system
from sys import exit, exc_info

from os.path import isdir, isfile

from unittest import main
from random import randint
from time import time

from amara.binderytools import bind_file, bind_string

from weightless import Reactor
from cq2utils import CQ2TestCase, getRequest, postRequest, wheelOfTime

from meresco.core import be

from simplexmlserver import dna

integrationTempdir = '/tmp/meresco-simple-xml-server-integration-test'
reactor = Reactor()

class SimpleXmlServerIntegrationTest(CQ2TestCase):

    def testIndexing(self):
        self.assertSruQuery(1, 'x.y.z=123', recordSchema='xml_based')
        self.assertSruQuery(1, 'data.part=one', recordSchema='xml_based')
        self.assertSruQuery(1, 'data.part=two', recordSchema='xml_based')


    def assertSruQuery(self, numberOfRecords, query, recordSchema):
        message = self._doQuery({'query':query, 'recordSchema': recordSchema})
        result = message.searchRetrieveResponse
        self.assertEquals(numberOfRecords, int(str(result.numberOfRecords)))
        return result

    def _doQuery(self, arguments, path="/sru"):
        queryArguments = {'version': '1.1', 'operation': 'searchRetrieve'}
        queryArguments.update(arguments)
        header, body = getRequest(reactor, port, path, queryArguments)
        return body

RECORD_0 = """<updateRequest>
    <srw:version xmlns:srw="http://www.loc.gov/zing/srw/">1.0</srw:version>
    <ucp:action xmlns:ucp="http://www.loc.gov/ucp">info:srw/action/1/replace</ucp:action>
    <ucp:recordIdentifier xmlns:ucp="http://www.loc.gov/ucp">meresco:record:1</ucp:recordIdentifier>
    <srw:record xmlns:srw="http://www.loc.gov/zing/srw/">
        <srw:recordPacking>xml</srw:recordPacking>
        <srw:recordSchema>xml_based</srw:recordSchema>
        <srw:recordData><x xmlns="http://example.org/namespace"><y><z>123</z></y></x>
        </srw:recordData>
    </srw:record>
</updateRequest>"""

RECORD_1 = """<updateRequest>
    <srw:version xmlns:srw="http://www.loc.gov/zing/srw/">1.0</srw:version>
    <ucp:action xmlns:ucp="http://www.loc.gov/ucp">info:srw/action/1/replace</ucp:action>
    <ucp:recordIdentifier xmlns:ucp="http://www.loc.gov/ucp">meresco:record:2</ucp:recordIdentifier>
    <srw:record xmlns:srw="http://www.loc.gov/zing/srw/">
        <srw:recordPacking>xml</srw:recordPacking>
        <srw:recordSchema>xml_based</srw:recordSchema>
        <srw:recordData><data xmlns="http://example.org/another_namespace"><part>one</part><part>two</part></data>
        </srw:recordData>
    </srw:record>
</updateRequest>
"""

def createDatabase(port):
    recordPacking = 'xml'
    start = time()
    print "Creating database in", integrationTempdir
    for nr, record in enumerate([RECORD_0, RECORD_1]):
        print "Sending RECORD_%s" % nr
        header, body = postRequest(reactor, port, '/update', record)
        if '200 Ok' not in header:
            print 'No 200 Ok response, but:'
            print header
            exit(123)
        if "srw:diagnostics" in body.xml():
            print body.xml()
            exit(1234)
    print "Finished creating database in %s seconds" % (time() - start)

if __name__ == '__main__':
    from sys import argv
    if not '--fast' in argv:
        system('rm -rf ' + integrationTempdir)
        system('mkdir --parents '+ integrationTempdir)

    port = randint(50000,60000)
    server = be(dna(reactor, 'localhost', portNumber=port, databasePath=integrationTempdir))
    server.once.observer_init()

    if '--fast' in argv and isdir(integrationTempdir):
        argv.remove('--fast')
        print "Reusing database in", integrationTempdir
    else:
        createDatabase(port)
    main()

