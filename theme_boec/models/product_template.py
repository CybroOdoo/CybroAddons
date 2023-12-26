# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    """Inherited product template for adding the field Hot Sale and Product
    Brand. While using the snippet  'Product Tab', the product with enabled
    Hot Sale will be display."""
    _inherit = "product.template"

    hot_deals = fields.Boolean(string="Hot Sale", help='The product or services'
                                                       'which are high in'
                                                       'demand at a particular'
                                                       'time or period')
    brand_id = fields.Many2one('product.brand', string="Product Brand",
                               help='Enabled product can filter from website'
                                    'by brand.')
