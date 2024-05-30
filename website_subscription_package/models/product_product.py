# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
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
from odoo import fields, models, _


class ProductProduct(models.Model):
    """Adding a new field for discounts for variants of subscription products
    second subscription."""
    _inherit = "product.product"

    subscription_discount = fields.Float(
        string="Discount(%)", help="Discount for second subscription.")

    def action_open_attribute_values_discount(self):
        """Set Discounts for variants of subscription products second
        subscription."""
        return {
            'type': 'ir.actions.act_window',
            'name': _("Product Variant Discount For 2nd subscription"),
            'res_model': 'product.product',
            'view_mode': 'tree',
            'views': [(self.env.ref('website_subscription_package.'
                                    'product_product_view_tree').id, 'list')],
            'context': {
                'search_default_product_tmpl_id': self.product_tmpl_id.id,
                'default_product_tmpl_id': self.product_tmpl_id.id},
            'target': 'current'}
