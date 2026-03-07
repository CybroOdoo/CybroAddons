# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: K Sai Saran Varma(odoo@cybrosys.com)
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
##############################################################################
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    """ Add contract reference in sale order line """
    _inherit = 'sale.order.line'

    contract_id = fields.Many2one(
        'subscription.contracts',
        string='Contracts',
        compute='_compute_contract_id',
        store=True,
        help='For adding Contracts in sale order line')

    @api.depends('product_id', 'order_id.partner_id', 'order_id.date_order')
    def _compute_contract_id(self):
        for line in self:
            line.contract_id = False

            if not line.product_id or not line.order_id.partner_id:
                continue

            line_date = line.order_id.date_order.date() if line.order_id.date_order else False
            if not line_date:
                continue

            contract = self.env['subscription.contracts'].search([
                ('partner_id', '=', line.order_id.partner_id.id),
                ('contract_line_ids.product_id', '=', line.product_id.id),
                ('date_start', '<=', line_date),
                '|',
                ('date_end', '=', False),
                ('date_end', '>=', line_date),
            ], order='date_start desc', limit=1)

            line.contract_id = contract