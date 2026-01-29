# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Prayag K (odoo@cybrosys.com)
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
from odoo import exceptions, api, models, _

"""Inherited sale.order.line for checking the limit of discount allowed for product and category"""


class SalesOrderDiscountLimit(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('discount')
    def _onchange_discount(self):
        """Checking the limit of discount allowed for products and category"""
        if not self.env.user.allow_discount:
            if self.product_id.product_tmpl_id.desc_limit > 0:
                if self.discount > self.product_id.product_tmpl_id.desc_limit:
                    raise exceptions.UserError(
                        _('You are not allowed to apply discount more than %s percentage '
                          'on this product. Please contact your administrator',
                          self.product_id.product_tmpl_id.desc_limit))
            elif self.product_id.categ_id.desc_limit > 0:
                if self.discount > self.product_id.categ_id.desc_limit:
                    raise exceptions.UserError(
                        _('You are not allowed to apply discount more than %s percentage '
                          'on this category of products. Please contact your administrator',
                          self.product_id.categ_id.desc_limit))
