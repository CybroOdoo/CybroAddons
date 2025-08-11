# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP (<https://www.cybrosys.com>)
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


class ProductBasedSalesCommission(models.Model):
    """Creating product based sales commission model."""
    _name = "product.based.sales.commission"
    _description = " Product Based Sales Commission"

    sale_commission_id = fields.Many2one("sales.commission",
                                         help="Sales commission",
                                         string='Sale Commission')
    product_id = fields.Many2one('product.product', string='Product',
                                 help="Product")
    commission = fields.Float(string='Commission %', help="Commission %")
