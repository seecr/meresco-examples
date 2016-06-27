## begin license ##
#
# "Meresco Examples" is a project demonstrating some of the
# features of various components of the "Meresco Suite".
# Also see http://meresco.org.
#
# Copyright (C) 2016 Seecr (Seek You Too B.V.) http://seecr.nl
#
# This file is part of "Meresco Examples"
#
# "Meresco Examples" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco Examples" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco Examples"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from seecr.test import IntegrationTestCase
from seecr.test.utils import getRequest
from meresco.components import lxmltostring
from meresco.xml import xpathFirst, xpath

class ApiTest(IntegrationTestCase):

    def testQuery(self):
        response = self.doSruQuery(query='*')
        self.assertEqual('2', xpathFirst(response, '//srw:numberOfRecords/text()'))
        self.assertEqual(set(['Example Program 1', 'Example Program 2']), set(xpath(response, '//srw:recordData/oai_dc:dc/dc:title/text()')))

    def testQueryWithDrilldown(self):
        response = self.doSruQuery(**{"query": 'dc:title = "Example Program"', "x-term-drilldown": "dc:date,dc:subject"})
        self.assertEqual('2', xpathFirst(response, '//srw:numberOfRecords/text()'))
        self.assertEqual(set(['Example Program 1', 'Example Program 2']), set(xpath(response, '//srw:recordData/oai_dc:dc/dc:title/text()')))

        ddItems = xpath(response, '//drilldown:term-drilldown/drilldown:navigator[@name="dc:date"]/drilldown:item')
        drilldown = [(i.text, i.attrib['count']) for i in ddItems]
        self.assertEqual([('2016', '2')], drilldown)

        ddItems = xpath(response, '//drilldown:term-drilldown/drilldown:navigator[@name="dc:subject"]/drilldown:item')
        drilldown = [(i.text, i.attrib['count']) for i in ddItems]
        self.assertEqual([('Search', '1'), ('Programming', '1')], drilldown)

    def testOai(self):
        header, body = getRequest(self.apiPort, '/oai', dict(verb="ListRecords", metadataPrefix="oai_dc"))
        records = xpath(body, '//oai:record/oai:metadata')
        self.assertEqual(2, len(records))

    def testRSS(self):
        header, body = getRequest(self.apiPort, '/rss', dict(query="dc:title=program"))
        items = xpath(body, "/rss/channel/item")
        self.assertEquals(2, len(items))
        self.assertEqual(set(["Example Program 1", "Example Program 2"]), set(xpath(body, "//item/title/text()")))
        self.assertEqual(set(["This is an example program about Search with Meresco", "This is an example program about Programming with Meresco"]), set(xpath(body, "//item/description/text()")))

    def doSruQuery(self, **arguments):
        queryArguments = {'version': '1.2', 'operation': 'searchRetrieve'}
        queryArguments.update(arguments)
        header, body = getRequest(self.apiPort, '/sru', queryArguments)
        return body
