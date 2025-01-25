# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gayathri V (odoo@cybrosys.com)
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
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    """Inheriting model 'account.move.line'"""
    _inherit = 'account.move.line'

    manual = fields.Boolean(string="Manual", help="True for manual",
                            default=True)
    date = fields.Date(string='Date', help="Date of payment", readonly=True)
    receipt_no = fields.Char(string='Receipt No',
                             help="Uniquely identifies the payment")

    @api.onchange('product_id')
    def _get_category_domain(self):
        """Set domain for invoice lines depend on selected category"""
        if self.move_id.fee_category_id:
            fee_types = self.env['education.fee.type'].search(
                [('category_id', '=', self.move_id.fee_category_id.id)])
            fee_list = []
            for fee in fee_types:
                fee_list.append(fee.product_variant_id.id)
            vals = {
                'domain': {
                    'product_id': [('id', 'in', tuple(fee_list))]
                }
            }
            return vals
