## begin license ##
#
# Drents Archief beoogt het Drents erfgoed centraal beschikbaar te stellen.
#
# Copyright (C) 2015-2016 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015-2016 Seecr (Seek You Too B.V.) http://seecr.nl
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

from meresco.components import XmlPrintLxml, RewritePartname, XmlXPath, FilterMessages, PeriodicCall, Schedule
from meresco.components.http import BasicHttpHandler, ObservableHttpServer, PathFilter, Deproxy
from meresco.components.log import ApacheLogWriter
from meresco.components.sru import SruRecordUpdate

from meresco.core import Observable
from meresco.core.alltodo import AllToDo
from meresco.core.processtools import setSignalHandlers, registerShutdownHandler

from meresco.oai import OaiJazz, OaiPmh, SuspendRegister, OaiAddDeleteRecordWithPrefixesAndSetSpecs
from meresco.oai.info import OaiInfo

from meresco.xml import namespaces

from os import makedirs
from os.path import dirname, abspath, join, isdir

from seecr.utils import DebugPrompt

from sys import stdout

from weightless.core import be, consume
from weightless.io import Reactor

from storage import StorageComponent
from storage.storageadapter import StorageAdapter

myPath = dirname(abspath(__file__))
dynamicPath = join(myPath, 'dynamic')

def main(reactor, port, statePath, **ignored):
    apacheLogStream = stdout

    oaiSuspendRegister = SuspendRegister()
    oaiJazz = be((OaiJazz(join(statePath, 'oai')),
        (oaiSuspendRegister,)
    ))
    storeComponent = StorageComponent(join(statePath, 'store'))

    scheduledCommitPeriodicCall = be(
        (PeriodicCall(reactor, message='commit', name='Scheduled commit', schedule=Schedule(period=1)),
            (AllToDo(),
                (storeComponent,),
                (oaiJazz,)
            )
        )
    )
    processingStates = [
        scheduledCommitPeriodicCall.getState(),
    ]

    return \
    (Observable(),
        (scheduledCommitPeriodicCall,),
        (DebugPrompt(reactor=reactor, port=port+1, globals=locals()),),
        (ObservableHttpServer(reactor=reactor, port=port),
            (ApacheLogWriter(apacheLogStream),),
            (Deproxy(),
                (BasicHttpHandler(),
                    (PathFilter('/oai', excluding=['/oai/info']),
                        (OaiPmh(repositoryName='Gateay',
                                adminEmail='info@example.org',
                                supportXWait=True
                            ),
                            (oaiJazz,),
                            (oaiSuspendRegister,),
                            (StorageAdapter(),
                                (storeComponent,),
                            ),
                        )
                    ),
                    (PathFilter('/oai/info'),
                        (OaiInfo(reactor=reactor, oaiPath='/oai'),
                            (oaiJazz,),
                        )
                    ),
                    (PathFilter('/update'),
                        (SruRecordUpdate(
                                sendRecordData=False,
                                logErrors=True,
                            ),
                            (RewritePartname('oai_dc'),
                                (FilterMessages(allowed=['delete']),
                                    (storeComponent,),
                                    (oaiJazz,),
                                ),
                                (FilterMessages(allowed=['add']),
                                    (XmlXPath(['srw:recordData/*'], namespaces=namespaces, fromKwarg="lxmlNode"),
                                        (XmlPrintLxml(fromKwarg='lxmlNode', toKwarg='data', pretty_print=False),
                                            (storeComponent,),
                                        ),
                                        (OaiAddDeleteRecordWithPrefixesAndSetSpecs(metadataPrefixes=['oai_dc']),
                                            (oaiJazz,),
                                        ),
                                    ),
                                )
                            )
                        )
                    ),
                )
            )
        ),
    )

def startServer(port, stateDir, **kwargs):
    setSignalHandlers()
    print 'Firing up Gateway Server.'
    statePath=abspath(stateDir)
    isdir(statePath) or makedirs(statePath)

    reactor = Reactor()
    dna = main(
            reactor=reactor,
            port=port,
            statePath=statePath,
            **kwargs
        )
    server = be(dna)
    consume(server.once.observer_init())

    registerShutdownHandler(statePath=statePath, server=server, reactor=reactor, shutdownMustSucceed=False)

    print 'Ready to rumble at %s' % port

    stdout.flush()
    reactor.loop()

