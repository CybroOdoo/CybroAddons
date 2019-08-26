# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sayooj A O(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models, api, fields


class Configuration(models.Model):
    """In this class the model pos.config is inherited
    to add a new boolean field in the settings of
    point of sale which is used to make enable/disable
    multiple order note in pos interface"""

    _inherit = 'pos.config'

    note_config = fields.Boolean(string='Order Line Note',
                                 help='Allow to write internal note in POS interface',
                                 default=True)
    iface_orderline_notes = fields.Boolean(string='Orderline Notes',
                                           help='Allow custom notes on Orderlines.',
                                           default=False, compute='_compute_iface_orderline_notes',
                                           readonly=False)

    @api.multi
    def _compute_iface_orderline_notes(self):
        """This is the compute function to disable
        the existing single order note facility
        in the point of sale interface"""
        if self.note_config:
            self.iface_orderline_notes = False

    @api.onchange('note_config')
    @api.depends('note_config')
    def _onchange_note_config(self):
        """This is the onchange function to disable/enable
        the existing single order note facility
            in the point of sale interface"""
        if self.note_config:
            self.iface_orderline_notes = False
        if not self.note_config:
            self.iface_orderline_notes = True
