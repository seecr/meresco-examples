#!/bin/bash
## begin license ##
#
#    Meresco Examples is a project demonstrating some of the features of
#    various Meresco components.
#    Copyright (C) 2010 Seek You Too (CQ2) http://www.cq2.nl
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

export PYTHONPATH=.:"$PYTHONPATH"
python2.5 _integrationtest.py
