# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class ProductProduct(models.Model):
    """ Make some of the product fields as storable to database"""
    _inherit = 'product.product'

    outgoing_qty = fields.Float(string="Outgoing quantity",
                                help="Quantity selling", readonly=True,
                                store=True)
    incoming_qty = fields.Float(string="Incoming quantity",
                                help="Quantity buying", readonly=True,
                                store=True)
    free_qty = fields.Float(string="Free quantity",
                            help="Balance quantity", readonly=True,
                            store=True)
    qty_available = fields.Float(string='Quantity available',
                                 help='Available quantity',
                                 readonly=True, store=True)
