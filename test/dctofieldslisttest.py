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

from seecr.test import SeecrTestCase, CallTrace
from meresco.examples.index.dctofieldslist import DcToFieldsList
from lxml.etree import XML, ElementTree
from weightless.core import consume


class DcToFieldsListTest(SeecrTestCase):

    def testOne(self):
        dcToFieldsList = DcToFieldsList()
        observer = CallTrace(emptyGeneratorMethods=['add'])
        dcToFieldsList.addObserver(observer)
        consume(dcToFieldsList.add(identifier='id:1', lxmlNode=ElementTree(XML(DC_RECORD))))
        self.assertEqual(['add'], observer.calledMethodNames())
        self.assertEqual({
                'fieldslist': [
                    ('dc:identifier', 'http://meresco.com?record=1'),
                    ('dc:description', 'This is an example program about Search with Meresco'),
                    ('dc:title', 'Example Program 1'),
                    ('dc:creator', 'Seecr'),
                    ('dc:publisher', 'Seecr'),
                    ('dc:date', '2016'),
                    ('dc:type', 'Example'),
                    ('dc:subject', 'Search'),
                    ('dc:language', 'en'),
                    ('dc:rights', 'Open Source')
                ],
                'identifier': 'id:1'
            }, observer.calledMethods[0].kwargs)


DC_RECORD = """
<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/      http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
    <dc:identifier xmlns:dc="http://purl.org/dc/elements/1.1/">http://meresco.com?record=1</dc:identifier>
    <dc:description xmlns:dc="http://purl.org/dc/elements/1.1/">This is an example program about Search with Meresco</dc:description>
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">Example Program 1</dc:title>
    <dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">Seecr</dc:creator>
    <dc:publisher xmlns:dc="http://purl.org/dc/elements/1.1/">Seecr</dc:publisher>
    <dc:date xmlns:dc="http://purl.org/dc/elements/1.1/">2016</dc:date>
    <dc:type xmlns:dc="http://purl.org/dc/elements/1.1/">Example</dc:type>
    <dc:subject xmlns:dc="http://purl.org/dc/elements/1.1/">Search</dc:subject>
    <dc:language xmlns:dc="http://purl.org/dc/elements/1.1/">en</dc:language>
    <dc:rights xmlns:dc="http://purl.org/dc/elements/1.1/">Open Source</dc:rights>
</oai_dc:dc>"""