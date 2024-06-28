# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP(odoo@cybrosys.com)
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
from odoo import api, fields, models
from odoo.tools import float_compare


class StockLot(models.Model):
    _inherit = "stock.lot"

    is_taken = fields.Boolean(string='Taken lot', default=False,
                              help='If enables this lot number is taken')

    @api.model
    def get_available_lots_for_pos(self, product_id):
        """Get available lots for a product suitable for the Point of Sale
        (PoS).This method retrieves the available lots for a specific product
        that are suitable for the Point of Sale (PoS) based on the configured
        removal strategy. The lots are sorted based on the expiration date or
        creation date,depending on the removal strategy."""
        company_id = self.env.company.id
        removal_strategy_id = (self.env['product.template'].browse(
            self.env['product.product'].browse(product_id).product_tmpl_id.id)
                               .categ_id.removal_strategy_id.method)
        if removal_strategy_id == 'fefo':
            lots = self.sudo().search(
                ["&", ["product_id", "=", product_id],"&",["is_taken","=",False],
                 "|", ["company_id", "=", company_id],
                 ["company_id", "=", False]],
                order='expiration_date asc')
        else:
            lots = self.sudo().search(
                ["&", ["product_id", "=", product_id], "|",
                 ["company_id", "=", company_id],
                 ["company_id", "=", False], ],
                order='create_date asc')
        lots = lots.filtered(lambda l: float_compare(
            l.product_qty, 0,
            precision_digits=l.product_uom_id.rounding) > 0)[:1]
        lots.is_taken = True
        return lots.mapped("name")
