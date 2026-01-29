# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aswathi PN (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class ProductProduct(models.Model):
    """Adding some new fields to the product model"""

    _inherit = 'product.product'

    rental = fields.Boolean(string='Rental',
                            help='To check the product is rental or not')
    category_id = fields.Many2one('rental.product.category',
                                  string='Rental Category',
                                  help='To add rental product category')
    security_amount = fields.Monetary(string='Security Amount',
                                      help='To add the security amount of the '
                                           'product')
    product_agreement_id = fields.Many2one('rental.product.agreement',
                                           string='Product Agreement',
                                           help='To add the product agreement')
