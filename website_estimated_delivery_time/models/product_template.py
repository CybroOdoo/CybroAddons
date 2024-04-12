# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ammu Raj (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    """This is for adding notebook on product.template model"""
    _inherit = 'product.template'

    overwrite_existing_config = fields.Boolean(
        string="Overwrite Existing Configuration",
        help="Overwrite the existing configuration in the wizard")
    delivery_time_visibility = fields.Boolean(string="Delivery Time Visibility",
                                              help="Delivery time visibility "
                                                   "based on this field")
    product_estimated_delivery_time_ids = fields.One2many(
        'product.estimated.delivery.time', 'product_id',
        string="Product Estimated Delivery Time",
        help="One2many for adding estimated delivery time in product")
