###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
"""Product extension model to track and fetch historical cost price."""
from datetime import datetime, time

from odoo import fields, models
from odoo.tools.float_utils import float_compare


class ProductProduct(models.Model):
    """Inheriting the product.product model and add price history tracking."""
    _inherit = 'product.product'

    def write(self, vals):
        """Record price history whenever standard_price changes."""
        if 'standard_price' in vals:
            new_cost = vals['standard_price']
            history_vals = []
            now = fields.Datetime.now()
            for product in self:
                if float_compare(
                    product.standard_price,
                    new_cost,
                    precision_digits=2,
                ) != 0:
                    company_id = product.company_id.id or self.env.company.id
                    history_vals.append({
                        'company_id': company_id,
                        'product_id': product.id,
                        'cost': new_cost,
                        'datetime': now,
                    })
            res = super().write(vals)
            if history_vals:
                self.env['price.history'].sudo().create(history_vals)
            return res
        return super().write(vals)

    def get_history_price(self, company_id, date=None):
        """to get the previous price of the product"""
        history_limit_date = date or fields.Datetime.now()
        if isinstance(history_limit_date, fields.Date) and not isinstance(
            history_limit_date, fields.Datetime,
        ):
            history_limit_date = datetime.combine(
                history_limit_date, time.max,
            )
        elif isinstance(history_limit_date, str) and len(history_limit_date) == 10:
            history_limit_date = f"{history_limit_date} 23:59:59"
        return self.env['price.history'].sudo().search([
            ('company_id', '=', company_id),
            ('product_id', 'in', self.ids),
            ('datetime', '<=', history_limit_date),
        ], order='datetime desc,id desc', limit=1).cost or 0.0
