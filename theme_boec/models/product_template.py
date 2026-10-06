# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models
from odoo.fields import Domain


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

    def _search_get_detail(self, website, order, options):
        res = super()._search_get_detail(website, order, options)
        if brand_ids := options.get('brand_ids'):
            res['base_domain'] = Domain.AND([
                res['base_domain'], Domain('brand_id', 'in', brand_ids),
            ])
        return res
