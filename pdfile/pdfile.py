#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# The PdFile library for Pure Data static patching.
#
# Copyright 2011 Pablo Duboue
# <pablo.duboue@gmail.com>
# http://duboue.net
#
# PdFile is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PdFile is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the gnu general public license
# along with PdFile.  If not, see <http://www.gnu.org/licenses/>.

"""
Tools for dealing with Pure Data files programmatically.

Creation and some basic understanding of PD files from Python.
"""


class PdFile(object):
    """
    A Pure Data File.
    """

    def __init__(self, filename, pos=None, size=None, font_size=10):
        pos = pos or [0, 0]
        size = size or [100, 100]
        self.filename = filename
        self.main = Patch(pos, size, font_size=font_size, main=True)

    def write(self):
        """
        Write to the file specified on the constructor.
        It opens and closes the file in this method.
        """
        file_ = open(self.filename, 'wb')
        self.main.write(file_)
        file_.close()

    @staticmethod
    def parse(filename):
        """
        Parse a Pure Data file.
        """
        #TODO
        pass


class Chunk(object):
    """
    A chunk in a PD file.

    It could be single-line or multi-line. Multi-line one should override the
    write method.
    """

    def __init__(self, chunktype, *args):
        """
        A generic chunk.
        """
        self.chunktype = chunktype
        self.remaining = list(args)

    def write_beginning(self, file_):
        """
        Write beginning of the chunk, # and chunktype.
        """
        file_.write('#')
        file_.write(self.chunktype)

    def write_end(self, file_):
        """
        Write end of the chunk, ;\r\n
        """
        file_.write(';\r\n')


    def write(self, file_):
        """
        Write a linear chunk, special chunks
        """
        self.write_beginning(file_)
        args = self.linearize()
        line = ''
        while args:
            if len(line) > 60:
                file_.write(line)
                file_.write('\r\n')
                line = ''
            line = "%s %s" % (line, str(args[0]))
            del args[0]
        file_.write(line)
        self.write_end(file_)

    def linearize(self):
        """
        Linearize all chunk arguments.
        """
        return list(self.remaining)
    

class ChunkWithPos(Chunk):
    """
    A chunk with a position associated with it.
    """

    def __init__(self, *args, **kwargs):
        """
        Pass the args to super class, fish out the position.
        """
        super(ChunkWithPos, self).__init__(*args)
        self.pos = kwargs.get('pos', [-1, -1])
        if 'x' in kwargs:
            self.pos[0] = kwargs['x']
        if 'y' in kwargs:
            self.pos[1] = kwargs['y']
            


class Patch(ChunkWithPos):
    """
    A patch within a PD file (or a patch itself).
    """

    class Mgr(object):
        """
        Container manager.
        """
        def __init__(self):
            self.elements = []
            self.elem_by_name = dict()
            self.connections = []
            self.object_count = 0
            self.last_pos = [0, 0]
            self.delta = [0, 50]

        def add(self, element, name=None):
            """
            Manage a new element.
            """
            if isinstance(element, PdObject):
                element.count = self.object_count
                self.object_count += 1
            if not name is None:
                self.elem_by_name[name] = element
            if element.pos[0] == -1:
                element.pos[0] = self.last_pos[0] + self.delta[0]
            if element.pos[1] == -1:
                element.pos[1] = self.last_pos[1] + self.delta[1]
            self.elements.append(element)
            self.last_pos = list(element.pos)
            return element

        def connect(self, obj1, outlet, obj2, inlet):
            """
            Manage a new connection.
            """
            if isinstance(obj1, basestring):
                obj1 = self.elem_by_name[obj1]
            if isinstance(obj2, basestring):
                obj2 = self.elem_by_name[obj2]
            self.connections.append(Connection(obj1, outlet, obj2, inlet))


    def __init__(self, pos=None, size=None, name=None, shown=False,
                 main=False, font_size=10, parent_pos=None):
        """
        Create a new patch, either a main one or a named one within an existing patch.
        """
        pos = pos or [0, 0] # avoid dangerous defaults
        size = size or [100, 100]
        parent_pos = parent_pos or [-1, -1]

        super(Patch, self).__init__('N', pos = parent_pos)

        self.screen_pos = pos
        self.size = size
        self.name = name
        self.shown = shown
        self.main = main
        self.font_size = font_size
        self.mgr = Patch.Mgr()
        
    def add(self, element, name=None):
        """
        Add an element to a patch.
        """
        return self.mgr.add(element, name)

    def connect(self, obj1, outlet, obj2, inlet):
        """
        Connect two objects, either by name or by object.
        """
        self.mgr.connect(obj1, outlet, obj2, inlet)

    def set_delta_add(self,**kwargs):
        """
        Set the delta coordinate applied to the last object added.
        """
        delta = kwargs.get('delta',self.mgr.delta)
        if 'x' in kwargs:
            delta[0] = kwargs['x']
        if 'y' in kwargs:
            delta[1] = kwargs['y']
        self.mgr.delta = delta

    def write(self, file_):
        """
        Write to an open file. This method will write all elements in this patch.
        """
        self.write_beginning(file_)
        file_.write(' canvas %d %d %d %d' %
          (self.screen_pos[0], self.screen_pos[1], self.size[0], self.size[1]))
        if self.main:
            file_.write(' %s' % (str(self.font_size)))
        else:
            if not self.name is None:
                file_.write(' %s' % (self.name))
                if self.shown:
                    file_.write(' 1')
                else:
                    file_.write(' 0')
        self.write_end(file_)
        for elem in self.mgr.elements:
            elem.write(file_)
        for conn in self.mgr.connections:
            conn.write(file_)
        if not self.main:
            self.write_beginning(file_)
            file_.write(' restore %d %d pd %s' %
              (self.pos[0], self.pos[1], self.name))
            self.write_end(file_)


class PdObject(ChunkWithPos):
    """
    An object in a patch.
    """

    def __init__(self, typename, *args, **kwargs):
        self.typename = typename
        super(PdObject, self).__init__('X', *args, **kwargs)
        self.count = 0

    def linearize(self):
        return ['obj', self.pos[0], self.pos[1], self.typename] + self.remaining


class PdMsg(ChunkWithPos):
    """
    A non-object Pure Data graphic chunk.
    """

    def __init__(self, *args, **kwargs):
        super(PdMsg, self).__init__('X', *args, **kwargs)

    def linearize(self):
        return ['msg', self.pos[0], self.pos[1]] + self.remaining


class Connection(Chunk):
    """
    A connection between two PdObjects.
    """

    def __init__(self, source, outlet, target, inlet):
        super(Connection, self).__init__('X')
        self.source = source
        self.outlet = outlet
        self.target = target
        self.inlet = inlet

    def linearize(self):
        return ['connect', self.source.count,
          self.outlet, self.target.count, self.inlet]
