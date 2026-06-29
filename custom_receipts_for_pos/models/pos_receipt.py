# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Techno Solutions
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class PosReceipt(models.Model):
    """
        This is an Odoo model for Point of Sale (POS).
        It creates a new model of pos.receipt for providing different types of
        receipt design.
    """
    _name = 'pos.receipt'
    _inherit = ['pos.load.mixin']
    _description = 'POS Receipts'

    def _load_pos_data_fields(self, config):
        """ Return the list of fields to be loaded into the POS """
        return ['id', 'name', 'design_receipt']

    name = fields.Char(string='Name', help='Name of the pos receipt')
    design_receipt = fields.Text(string='Receipt XML',
                                 help='Add your customised receipts for pos')
