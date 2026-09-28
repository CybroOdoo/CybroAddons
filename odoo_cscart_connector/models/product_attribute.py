# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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

from odoo import models, fields


class ProductAttribute(models.Model):
    """
    Extends product.attribute to store the mapped CS-Cart Feature ID.
    """
    _inherit = "product.attribute"

    cs_cart_feature_id = fields.Integer(
        string="CS-Cart Feature ID",
        index=True,
        copy=False,
    )


class ProductAttributeValue(models.Model):
    """
    Extends product.attribute.value to store the mapped CS-Cart Variant ID.
    """
    _inherit = "product.attribute.value"

    cs_cart_variant_id = fields.Integer(
        string="CS-Cart Variant ID",
        index=True,
        copy=False,
    )
