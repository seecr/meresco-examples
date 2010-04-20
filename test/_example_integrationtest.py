# encoding: utf-8
## begin license ##
#
#    Meresco Examples is a project demonstrating some of the features of
#    various Meresco components.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#
#    This file is part of Meresco Examples.
#
#    Meresco Examples is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Examples is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Examples; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
from os import getuid
assert getuid() != 0, "Do not run tests as 'root'"

from os import system                             #DO_NOT_DISTRIBUTE
from sys import path as sysPath                   #DO_NOT_DISTRIBUTE
system('find .. -name "*.pyc" | xargs rm -f')     #DO_NOT_DISTRIBUTE
                                                  #DO_NOT_DISTRIBUTE
from glob import glob                             #DO_NOT_DISTRIBUTE
for path in glob('../deps.d/*'):                  #DO_NOT_DISTRIBUTE
    sysPath.insert(0, path)                       #DO_NOT_DISTRIBUTE
sysPath.insert(0,'..')                            #DO_NOT_DISTRIBUTE

from os import system
from sys import exit, exc_info

from os.path import isdir, isfile

from unittest import main
from random import randint
from time import time
from glob import glob

from amara.binderytools import bind_file, bind_string

from weightless import Reactor
from cq2utils import CQ2TestCase, getRequest, postRequest, wheelOfTime

from merescocore.framework import be

from meresco.examples.dna.server import dna, config

integrationTempdir = '/tmp/meresco-integration-test'
reactor = Reactor()

class IntegrationTest(CQ2TestCase):

    def testExplain(self):
        header, body = getRequest(reactor, port, '/sru', {})
        explainResponse = body.explainResponse
        self.assertEquals(config['host'], str(explainResponse.record.recordData.explain.serverInfo.host))

        portNumber = int(explainResponse.record.recordData.explain.serverInfo.port)
        self.assertTrue(50000 < portNumber < 60000, portNumber)

    def testIndex(self):
        self.assertSruQuery(2, 'dc="Seek You Too"')
        self.assertSruQuery(2, 'dc.title = program')
        self.assertSruQuery(1, 'dc.identifier="http://meresco.com?record=2"')

    def testDrilldown(self):
        result = self.doDrilldown('dc.rights="Open Source"', 'dc.subject')
        navigator = result.extraResponseData.drilldown.term_drilldown.navigator

        self.assertEquals(1, len(navigator), result.xml())
        self.assertEquals('dc.subject', str(navigator.name))
        self.assertEquals(2, len(navigator.item))
        itemValues = [(item.count, str(item)) for item in navigator.item]
        self.assertEquals([(1, 'Programming'), (1, 'Search')], itemValues)

    def testRSS(self):
        body = self._doQuery({'query': 'dc.title = program'}, path="/rss")
        items = [(str(item.title), str(item.description), str(item.link).split('?', 1)[1]) for item in body.rss.channel.item]
        self.assertEquals(2, len(items))
        self.assertEquals([('Example Program 1', 'This is an example program about Search with Meresco', 'operation=searchRetrieve&version=1.1&query=dc.identifier%3Dhttp%3A//meresco.com%3Frecord%3D1'), ('Example Program 2', 'This is an example program about Programming with Meresco', 'operation=searchRetrieve&version=1.1&query=dc.identifier%3Dhttp%3A//meresco.com%3Frecord%3D2')], items)

    def testOaiIdentify(self):
        header, body = getRequest(reactor, port, '/oai', {'verb': 'Identify'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/xml; charset=utf-8', header)
        self.assertEquals('Meresco Example Repository', body.OAI_PMH.Identify.repositoryName)
        self.assertEquals('admin@example.org', body.OAI_PMH.Identify.adminEmail)

    def testOaiListRecords(self):
        header, body = getRequest(reactor, port, '/oai', {'verb': 'ListRecords', 'metadataPrefix': 'oai_dc'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/xml; charset=utf-8', header)
        self.assertEquals(3, len(body.OAI_PMH.ListRecords.record))

    def testDeleteRecord(self):
        self.assertSruQuery(0, 'dc.identifier="http://meresco.com?record=3"')
        header, body = getRequest(reactor, port, '/oai', {'verb': 'ListRecords', 'metadataPrefix': 'oai_dc'})
        self.assertEquals('deleted', body.OAI_PMH.ListRecords.record[2].header.status)

    def doDrilldown(self, query, drilldownField):
        message = self._doQuery({'query':query, 'x-term-drilldown': drilldownField})
        result = message.searchRetrieveResponse
        return result

    def assertSruQuery(self, numberOfRecords, query):
        message = self._doQuery({'query':query})
        result = message.searchRetrieveResponse
        self.assertEquals(numberOfRecords, int(str(result.numberOfRecords)))
        return result

    def _doQuery(self, arguments, path="/sru"):
        queryArguments = {'version': '1.1', 'operation': 'searchRetrieve'}
        queryArguments.update(arguments)
        header, body = getRequest(reactor, port, path, queryArguments)
        return body

def createDatabase(port):
    recordPacking = 'xml'
    start = time()
    print "Creating database in", integrationTempdir
    sourceFiles = glob('harvester_output/*.updateRequest')
    for updateRequestFile in sorted(sourceFiles):
        print 'Sending:', updateRequestFile
        header, body = postRequest(reactor, port, '/update', open(updateRequestFile).read())
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
    server = be(dna(reactor, config['host'], portNumber=port, databasePath=integrationTempdir))
    server.once.observer_init()

    if '--fast' in argv and isdir(integrationTempdir):
        argv.remove('--fast')
        print "Reusing database in", integrationTempdir
    else:
        createDatabase(port)
    main()
