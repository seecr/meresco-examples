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

from weightless.core import compose, Yield

from meresco.lucene import UNTOKENIZED_PREFIX

class DcFields(object):
    def __init__(self, observable, untokenizedFieldnames):
        self._observable = observable
        self._untokenizedFieldnames = untokenizedFieldnames

    def fieldsFor(self, fieldname, value):
        fields = []
        for o in compose(self._fieldsFor(fieldname, value)):
            if callable(o) or o is Yield:
                yield o
                continue
            f, v = o
            fields.append((f, v))
        raise StopIteration(fields)
        yield

    def _fieldsFor(self, fieldname, value):
        yield '__all__', value
        yield fieldname, value
        yield self._untokenizedField(fieldname, value)

    def _untokenizedField(self, fieldname, value):
        name = untokenizedFieldname(fieldname)
        if name in self._untokenizedFieldnames:
            yield name, value

def untokenizedFieldname(fieldname):
    return UNTOKENIZED_PREFIX + fieldname
