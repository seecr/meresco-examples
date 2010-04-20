## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2007-2009 Seek You Too (CQ2) http://www.cq2.nl
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
from sys import stdout

from os.path import join, isdir
from os import makedirs

from merescocore.framework import be, Observable, TransactionScope, ResourceManager, Transparant

from merescocore.components import StorageComponent, FilterField, RenameField, XmlParseLxml, XmlXPath, XmlPrintLxml, Xml2Fields, Venturi, FilterMessages, Amara2Lxml, RewritePartname, Rss, RssItem, Lxml2Amara
from merescocomponents.facetindex import Drilldown, LuceneIndex, CQL2LuceneQuery, Fields2LuceneDocumentTx
from merescocomponents.facetindex.tools import unlock
from merescocore.components.drilldown import SRUTermDrilldown, DrilldownFieldnames
from merescocore.components.http import PathFilter, ObservableHttpServer
from merescocore.components.http.webrequestserver import WebRequestServer
from merescocore.components.sru import SruParser, SruHandler, SRURecordUpdate
from merescocomponents.oai import OaiPmh, OaiJazz, OaiAddRecordWithDefaults

from weightless import Reactor

DRILLDOWN_PREFIX = 'drilldown.'
drilldownFieldnames = ['drilldown.dc.subject']
unqualifiedTermFields = [('dc', 1.0)]

def createUploadHelix(indexHelix, storageComponent, oaiJazz):
    fields2LuceneDocument = \
        (ResourceManager('record', lambda resourceManager: Fields2LuceneDocumentTx(resourceManager, untokenized=drilldownFieldnames)),
            indexHelix
        )

    indexingHelix = \
        (Transparant(),
            fields2LuceneDocument,
            (FilterField(lambda name: DRILLDOWN_PREFIX + name in drilldownFieldnames),
                (RenameField(lambda name: DRILLDOWN_PREFIX + name),
                    fields2LuceneDocument
                )
            )
        )

    return \
        (TransactionScope('batch'),
            (TransactionScope('record'),
                (Venturi(
                    should=[
                        ('metadata', '/document:document/document:part[@name="metadata"]/text()'),
                        ('header', '/document:document/document:part[@name="header"]/text()')
                    ],
                    namespaceMap={'document': 'http://meresco.org/namespace/harvester/document'}),
                    (FilterMessages(allowed=['delete']),
                        indexHelix
                    ),
                    (XmlXPath(['/oai:metadata/oai_dc:dc']),
                        (XmlPrintLxml(),
                            (RewritePartname('oai_dc'),
                                (storageComponent,)
                            )
                        ),
                        (Xml2Fields(),
                            indexingHelix,
                            (RenameField(lambda name: "dc"),
                                indexingHelix
                            ),
                        ),
                        (RewritePartname('oai_dc'),
                            (OaiAddRecordWithDefaults(metadataFormats=[
                                ('mods', 'http://www.loc.gov/standards/mods/v3/mods-3-3.xsd', 'http://www.loc.gov/mods/v3'),
                                ('oai_dc', 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd', 'http://www.openarchives.org/OAI/2.0/oai_dc/')
                            ],
                            sets=[('meresco','meresco')]),
                                (oaiJazz,)
                            )
                        )
                    ),
                    (XmlXPath(['/oai:header']),
                        (Lxml2Amara(),
                            (oaiJazz,)
                        )
                    )
                )
            )
        )

def dna(reactor,  host, portNumber, databasePath):
    unlock(join(databasePath, 'index'))

    storageComponent = StorageComponent(join(databasePath, 'storage'), partsRemovedOnDelete=['oai_dc'])
    drilldownComponent = Drilldown(drilldownFieldnames, transactionName="batch")

    indexHelix = \
        (LuceneIndex(join(databasePath, 'index'), transactionName="batch"),
            (drilldownComponent,)
        )

    oaiJazz = OaiJazz(join(databasePath, 'oai', 'data'))

    serverUrl = 'http://%s:%s' % (host, portNumber)

    return \
        (Observable(),
            (ObservableHttpServer(reactor, portNumber),
                (PathFilter("/sru"),
                    (SruParser(host=host, port=portNumber, defaultRecordSchema='oai_dc', defaultRecordPacking='xml'),
                        (SruHandler(),
                            (CQL2LuceneQuery(unqualifiedTermFields),
                                indexHelix
                            ),
                            (storageComponent,),
                            (SRUTermDrilldown(),
                                (DrilldownFieldnames(
                                    lambda field: DRILLDOWN_PREFIX + field,
                                    lambda field: field[len(DRILLDOWN_PREFIX):]),
                                        (drilldownComponent,)
                                ),
                                (CQL2LuceneQuery(unqualifiedTermFields),
                                    indexHelix
                                ),
                            )
                        )
                    )
                ),
                (PathFilter("/update"),
                    (SRURecordUpdate(),
                        (Amara2Lxml(),
                            createUploadHelix(indexHelix, storageComponent, oaiJazz)
                        )
                    )
                ),
                (PathFilter('/rss'),
                    (Rss(   title = 'Meresco',
                            description = 'RSS feed for Meresco',
                            link = 'http://meresco.org',
                            maximumRecords = 15),
                        (CQL2LuceneQuery(unqualifiedTermFields),
                            indexHelix
                        ),
                        (RssItem(
                                nsMap={
                                    'dc': "http://purl.org/dc/elements/1.1/",
                                    'oai_dc': "http://www.openarchives.org/OAI/2.0/oai_dc/"
                                },
                                title = ('oai_dc', '/oai_dc:dc/dc:title/text()'),
                                description = ('oai_dc', '/oai_dc:dc/dc:description/text()'),
                                linkTemplate = serverUrl +   '/sru?operation=searchRetrieve&version=1.1&query=dc.identifier%%3D%(identifier)s',
                                identifier = ('oai_dc', '/oai_dc:dc/dc:identifier/text()')),
                            (storageComponent, )
                        ),
                    )
                ),
                (PathFilter('/oai'),
                    (WebRequestServer(),
                        (OaiPmh(repositoryName='Meresco Example Repository',
                            adminEmail='admin@example.org'),
                            (oaiJazz,),
                            (storageComponent,),
                        )
                    )
                ),
            )
        )


config = {
    'host': 'localhost',
    'port': 8000
}

if __name__ == '__main__':
    databasePath = '/tmp/meresco'
    if not isdir(databasePath):
        makedirs(databasePath)

    reactor = Reactor()
    server = be(dna(reactor, config['host'], config['port'], databasePath))
    server.once.observer_init()

    print "Server listening on", config['host'], "at port", config['port']
    print "   - database:", databasePath, "\n"
    stdout.flush()
    reactor.loop()
