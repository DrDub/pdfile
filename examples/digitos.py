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
# Copyright 2011, Pablo Duboue <pablo.duboue@gmail.com>
# Licenced under the terms of the GPLv2 or later


"""
Make a small Pure Data patch that transforms a digit to a symbol of
its spelled-out counterpart.
"""

from pdfile import pdfile

if __name__ == "__main__":
    DIGITS = [ 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete',
               'ocho', 'nueve' ]

    __pd__ = pdfile.PdFile("digitos.pd", [10, 10], [300, 300], 16)
    __pd__.main.add(pdfile.PdObject('inlet'), 'in')
    __pd__.main.add(pdfile.PdObject('outlet'), 'out')
    __pd__.main.add(pdfile.PdObject('select',
                    *[ x+1 for x in range(len(DIGITS)) ]), 'select')
    __pd__.main.connect('in', 0, 'select', 0)
    for num in range(len(DIGITS)):
        digit = 'digit_' + str(num + 1)
        __pd__.main.add(pdfile.PdObject('symbol', DIGITS[num]), digit)
        __pd__.main.connect('select', num, digit, 0)
        __pd__.main.connect(digit, 0, 'out', 0)

    __pd__.write()
