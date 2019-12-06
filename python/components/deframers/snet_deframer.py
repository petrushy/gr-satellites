#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 Daniel Estevez <daniel@destevez.net>.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
# 
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.

from gnuradio import gr, blocks, digital
from ... import snet_deframer as deframer
from ...hier.sync_to_pdu import sync_to_pdu
from ...utils.options_block import options_block

_syncword = '00000100110011110101111111001000'

class snet_deframer(gr.hier_block2, options_block):
    """
    Hierarchical block to deframe the S-NET custom framing.

    The input is a float stream of soft symbols. The output are PDUs
    with frames.

    Args:
        syncword_threshold: number of bit errors allowed in syncword (int)
        options: Options from argparse
    """
    def __init__(self, syncword_threshold = None, options = None):
        gr.hier_block2.__init__(self, "snet_deframer",
            gr.io_signature(1, 1, gr.sizeof_float),
            gr.io_signature(0, 0, 0))
        options_block.__init__(self, options)
        
        self.message_port_register_hier_out('out')

        if syncword_threshold is None:
            syncword_threshold = self.options.syncword_threshold

        self.invert = blocks.multiply_const_ff(-1, 1)
        self.slicer = digital.binary_slicer_fb()
        self.deframer = sync_to_pdu(packlen = 8 * 512,\
                                    sync = _syncword,\
                                    threshold = syncword_threshold)
        self.fec = deframer(self.options.verbose_fec)
        
        self.connect(self, self.invert, self.slicer, self.deframer)
        self.msg_connect((self.deframer, 'out'), (self.fec, 'in'))
        self.msg_connect((self.fec, 'out'), (self, 'out'))

    _default_sync_threshold = 4
        
    @classmethod
    def add_options(cls, parser):
        """
        Adds S-NET deframer specific options to the argparse parser
        """
        parser.add_argument('--syncword_threshold', type = int, default = cls._default_sync_threshold, help = 'Syncword bit errors [default=%(default)r]')
        parser.add_argument('--verbose_fec', action = 'store_true', help = 'Verbose FEC decoder')