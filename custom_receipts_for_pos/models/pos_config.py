# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
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
                                 string='Receipt XML', help='Custom receipt design XML content')
    logo = fields.Binary(related='company_id.logo', string='Logo',
                         readonly=False, help='Company logo to be displayed on the receipt')
    is_custom_receipt = fields.Boolean(string='Is Custom Receipt',
                                       help='Indicates the receipt  design is '
                                            'custom or not')
