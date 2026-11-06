# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul (odoo@cybrosys.com)
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
import datetime

from odoo import api, fields, models
from odoo.tools import float_compare


class ProductProduct(models.Model):
    """Inheriting the product.product model to keep a cost history"""
    _inherit = 'product.product'

    @api.model_create_multi
    def create(self, vals_list):
        """Log the initial cost of the new products"""
        products = super().create(vals_list)
        for product, vals in zip(products, vals_list):
            if vals.get('standard_price'):
                product._log_standard_price()
        return products

    def write(self, vals):
        """Log the new cost whenever the standard price is changed"""
        result = super().write(vals)
        if 'standard_price' in vals:
            self._log_standard_price()
        return result

    def _log_standard_price(self):
        """Create a price history record for the current standard price,
        unless the latest record already holds the same cost"""
        history = self.env['price.history'].sudo()
        company = self.env.company
        precision = self.env['decimal.precision'].precision_get(
            'Product Price')
        for product in self:
            last = history.search([
                ('company_id', '=', company.id),
                ('product_id', '=', product.id)],
                order='datetime desc,id desc', limit=1)
            if not last or float_compare(
                    last.cost, product.standard_price,
                    precision_digits=precision):
                history.create({
                    'company_id': company.id,
                    'product_id': product.id,
                    'cost': product.standard_price,
                })

    def get_history_price(self, company_id, date=None):
        """to get the previous price of the product"""
        if date and not isinstance(date, datetime.datetime):
            date = datetime.datetime.combine(date, datetime.time.max)
        return self.env['price.history'].search([
            ('company_id', '=', company_id),
            ('product_id', 'in', self.ids),
            ('datetime', '<=', date or fields.Datetime.now())],
            order='datetime desc,id desc', limit=1).cost or 0.0
