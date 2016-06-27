# -*- coding: utf-8 -*-
## begin license ##
#
# Drents Archief beoogt het Drents erfgoed centraal beschikbaar te stellen.
#
# Copyright (C) 2012-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015-2016 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
#
# This file is part of "Drents Archief"
#
# "Drents Archief" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Drents Archief" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Drents Archief"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from os.path import dirname, abspath, join
from sys import stdout

from weightless.core import be, consume
from weightless.http import HttpRequest1_1, SocketPool
from weightless.io import Reactor

from meresco.core import Observable
from meresco.core.alltodo import AllToDo
from meresco.core.processtools import setSignalHandlers, registerShutdownHandler

from meresco.components.http import BasicHttpHandler, ObservableHttpServer, PathFilter
from meresco.components import PeriodicDownload, FilterMessages, XmlXPath, XmlParseLxml, PeriodicCall, Schedule
from meresco.components.log import LogCollector, ApacheLogWriter, HandleRequestLog, LogComponent
from meresco.distributed import CompositeState

from meresco.lucene.lucenecommit import LuceneCommit
from meresco.lucene.queryexpressiontolucenequerydict import QueryExpressionToLuceneQueryDict

from meresco.oai import OaiDownloadProcessor, UpdateAdapterFromOaiDownloadProcessor

from seecr.utils import DebugPrompt
from threading import Thread
from meresco.lucene import LuceneSettings, DrilldownField, FieldsListToLuceneDocument
from meresco.pylucene import getJVM

from meresco.lucene import Lucene, MultiLucene, UNTOKENIZED_PREFIX
from meresco.lucene.adaptertolucenequery import AdapterToLuceneQuery
from meresco.lucene.remote import LuceneRemoteService
from meresco.lucene.fieldregistry import FieldRegistry

from .dctofieldslist import DcToFieldsList
from .dcfields import DcFields

LUCENE_VM = getJVM()

myPath = dirname(abspath(__file__))
dynamicPath = join(myPath, 'dynamic')
binDir = join(dirname(dirname(myPath)), "bin")

def untokenizedFieldname(fieldname):
    return UNTOKENIZED_PREFIX + fieldname

UNQUALIFIED_TERM_FIELDS = [('__all__', 1.0)]
drilldownFields = [
    DrilldownField(untokenizedFieldname('dc:date')),
    DrilldownField(untokenizedFieldname('dc:subject')),
]
untokenizedFieldnames = [f.name for f in drilldownFields]

DEFAULT_CORE = 'oai_dc'

def luceneAndReaderConfig(reactor, statePath, defaultLuceneSettings, httpRequestAdapter, serverPort):
    fieldRegistry = FieldRegistry(drilldownFields=drilldownFields)
    luceneIndex = be((Lucene(
            host='127.0.0.1',
            port=serverPort,
            name=DEFAULT_CORE,
            settings=defaultLuceneSettings.clone(fieldRegistry=fieldRegistry)
        ),
        (httpRequestAdapter,)
    ))
    return luceneIndex

def readerMain(reactor, statePath, port, downloadProcessorStates, defaultLuceneSettings, serverPort):
    apacheLogStream = stdout

    http11Request = be(
        (HttpRequest1_1(),
            (SocketPool(reactor=reactor, unusedTimeout=5, limits=dict(totalSize=100, destinationSize=10)),),
        )
    )
    luceneIndex = luceneAndReaderConfig(reactor, statePath, defaultLuceneSettings.clone(readonly=True), http11Request, serverPort)

    return \
    (Observable(),
        (DebugPrompt(reactor=reactor, port=port+1, globals=locals()),),
        (ObservableHttpServer(reactor=reactor, port=port),
            (LogCollector(),
                (ApacheLogWriter(apacheLogStream),),
                (HandleRequestLog(),
                    (BasicHttpHandler(),
                        (PathFilter('/lucene'),
                            (LuceneRemoteService(reactor=reactor),
                                (AdapterToLuceneQuery(
                                        defaultCore=DEFAULT_CORE,
                                        coreConverters={
                                            DEFAULT_CORE: QueryExpressionToLuceneQueryDict(UNQUALIFIED_TERM_FIELDS, luceneSettings=luceneIndex.settings),
                                        }
                                    ),
                                    (MultiLucene(host='localhost', port=serverPort, defaultCore=DEFAULT_CORE),
                                        (luceneIndex,),
                                        (http11Request,),
                                    )
                                ),
                            )
                        )
                    ),
                )
            )
        ),
    )


def writerMain(writerReactor, readerReactor, readerPort, statePath, serverPort, gatewayPort):
    apacheLogStream = stdout

    http11Request = be(
        (HttpRequest1_1(),
            (SocketPool(reactor=writerReactor, unusedTimeout=5, limits=dict(totalSize=100, destinationSize=10)),),
        )
    )
    indexCommitTimeout = 30

    defaultLuceneSettings = LuceneSettings(
            commitTimeout=indexCommitTimeout,
            readonly=False,
        )

    luceneWriter = luceneAndReaderConfig(writerReactor, statePath, defaultLuceneSettings, http11Request, serverPort)

    periodicDownload = PeriodicDownload(
        writerReactor,
        host='localhost',
        port=gatewayPort,
        name='gateway',
        autoStart=True)

    oaiDownload = OaiDownloadProcessor(
        path='/oai',
        metadataPrefix='oai_dc',
        workingDirectory=join(statePath, 'harvesterstate', 'gateway'),
        xWait=True,
        name='gateway',
        autoCommit=False)

    scheduledCommitPeriodicCall = be(
        (PeriodicCall(writerReactor, message='commit', name='Scheduled commit', schedule=Schedule(period=1), initialSchedule=Schedule(period=1)),
            (AllToDo(),
                (periodicDownload,),
                (LuceneCommit(host='localhost', port=serverPort,),
                    (LogComponent(),),
                    (http11Request,),
                )
            )
        )
    )
    downloadProcessorStates = [
        CompositeState(oaiDownload.getState(), periodicDownload.getState()),
        scheduledCommitPeriodicCall.getState(),
    ]

    readerServer = readerMain(
            reactor=readerReactor,
            statePath=statePath,
            port=readerPort,
            downloadProcessorStates=downloadProcessorStates,
            defaultLuceneSettings=defaultLuceneSettings,
            serverPort=serverPort,
        )

    writerServer = \
    (Observable(),
        (scheduledCommitPeriodicCall,),
        (DebugPrompt(reactor=writerReactor, port=readerPort-1, globals=locals()),),
        (periodicDownload,
            (XmlParseLxml(fromKwarg="data", toKwarg="lxmlNode", parseOptions=dict(huge_tree=True, remove_blank_text=True)),
                (oaiDownload,
                    (UpdateAdapterFromOaiDownloadProcessor(),
                        (FilterMessages(allowed=['add']),
                            (XmlXPath(['/oai:record/oai:metadata/document:document/document:part[@name="record"]/text()'], fromKwarg='lxmlNode', toKwarg='data'),
                                (XmlParseLxml(fromKwarg='data', toKwarg='lxmlNode'),
                                    (XmlXPath(['/oai:record/oai:metadata/oai_dc:dc'], fromKwarg='lxmlNode'),
                                        (DcToFieldsList(),
                                            (FieldsListToLuceneDocument(
                                                    fieldRegistry=luceneWriter.settings.fieldRegistry,
                                                    untokenizedFieldnames=untokenizedFieldnames,
                                                    indexFieldFactory=DcFields),
                                                (luceneWriter,),
                                            )
                                        )
                                    )
                                )
                            )
                        ),
                        (FilterMessages(allowed=['delete']),
                            (luceneWriter,),
                        )
                    )
                )
            )
        ),
    )
    return readerServer, writerServer


def startServer(port, stateDir, serverPort, gatewayPort, **ignored):
    setSignalHandlers()
    print 'Firing up Index Server.'

    statePath = abspath(stateDir)
    writerReactor = Reactor()
    readerReactor = Reactor()

    reader, writer = writerMain(
            writerReactor=writerReactor,
            readerReactor=readerReactor,
            readerPort=port,
            statePath=statePath,
            serverPort=serverPort,
            gatewayPort=gatewayPort,
        )

    readerServer = be(reader)
    writerServer = be(writer)

    def startReader():
        LUCENE_VM.attachCurrentThread()
        consume(readerServer.once.observer_init())
        readerReactor.loop()

    consume(writerServer.once.observer_init())

    registerShutdownHandler(statePath=statePath, server=writerServer, reactor=writerReactor, shutdownMustSucceed=False)

    tReader = Thread(target=startReader)
    tReader.setDaemon(True)
    tReader.start()

    print "Ready to rumble at port %s" % port
    stdout.flush()

    writerReactor.loop()
