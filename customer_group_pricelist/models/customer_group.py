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


class CustomerGroup(models.Model):
    """New model to create customer group price list."""
    _name = 'customer.group'
    _description = 'Create Customer Groups'

    name = fields.Char(string='Name', help='Name of the Pricelist')
    contact_ids = fields.Many2many('res.partner', string='Contacts',
                                   help='Add contacts to the customer group')
    pricelist_id = fields.Many2one('product.pricelist',
                                   string='PriceList',
                                   help='Add Pricelist for apply on the '
                                        'customer group')
