# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models


class ProductProduct(models.Model):
    """To add a Prestashop id"""
    _inherit = "product.product"

    prestashop = fields.Integer(string="Prestashop Id",
                                help="Prestashop Id of the product")

    is_delivery_product = fields.Boolean(string="Prestashop delivery product",
                                         help="Identify the product as the "
                                              "Prestashop delivery product")
    is_discount_product = fields.Boolean(string="Prestashop discount product",
                                         help="Identify the product as the "
                                              "Prestashop discount product")


