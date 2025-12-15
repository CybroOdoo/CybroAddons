# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Neeraj JR (<https://www.cybrosys.com>)
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

class PosConfig(models.Model):
    """
        This is an Odoo model for Point of Sale (POS).
        It inherits the 'pos.config' model to add new fields.
    """
    _inherit = 'pos.config'

    receipt_design_id = fields.Many2one('pos.receipt', string='Receipt Design',
                                     help='Choose any receipt design')
    design_receipt = fields.Text(related='receipt_design_id.design_receipt',
                                 string='Receipt XML')
    logo = fields.Binary(related='receipt_design_id.logo', string='Logo',
                         readonly=False)
    is_custom_receipt = fields.Boolean(string='Is Custom Receipt',
                                       help='Indicates the receipt  design is '
                                            'custom or not')
    design_receipt_font_style = fields.Char(
        related='receipt_design_id.design_receipt_font_style',
        string='Receipt Font Style'
    )