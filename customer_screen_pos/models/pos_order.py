# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP (odoo@cybrosys.com)
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
from functools import partial
from odoo import api, fields, models


class PosOrder(models.Model):
    """Extend functionality of Point of Sale Order"""
    _inherit = 'pos.order'

    rating = fields.Selection([
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
    ], default='5', string="Rating", help="Rating Stars")
    rating_text = fields.Text(string="Feedback", help='Feedback of customers')

    @api.model
    def _order_fields(self, ui_order):
        """Function to fetch order details from POS and return to POS order"""
        process_line = partial(self.env['pos.order.line']._order_line_fields,
                               session_id=ui_order['pos_session_id'])
        pos_order_review = self.env['pos.order.review'].search(
            [('pos_order_ref', '=', ui_order['name'])])
        return {
            'user_id': ui_order['user_id'] or False,
            'session_id': ui_order['pos_session_id'],
            'lines': [process_line(lines) for lines in ui_order['lines']] if
            ui_order[
                'lines'] else False,
            'pos_reference': ui_order['name'],
            'sequence_number': ui_order['sequence_number'],
            'partner_id': ui_order['partner_id'] or False,
            'date_order': ui_order['date_order'],
            'fiscal_position_id': ui_order['fiscal_position_id'],
            'pricelist_id': ui_order['pricelist_id'],
            'amount_paid': ui_order['amount_paid'],
            'last_order_preparation_change': ui_order['last_order_preparation_change'],
            'amount_total': ui_order['amount_total'],
            'amount_tax': ui_order['amount_tax'],
            'amount_return': ui_order['amount_return'],
            'company_id': self.env['pos.session'].browse(
                ui_order['pos_session_id']).company_id.id,
            'to_invoice': ui_order[
                'to_invoice'] if "to_invoice" in ui_order else False,
            'shipping_date': ui_order['shipping_date'] if "shipping_date" in ui_order else False,
            'is_tipped': ui_order.get('is_tipped', False),
            'tip_amount': ui_order.get('tip_amount', 0),
            'access_token': ui_order.get('access_token', ''),
            'rating': ("1" if pos_order_review.review_star == "star1" else
                       "2" if pos_order_review.review_star == "star2" else
                       "3" if pos_order_review.review_star == "star3" else
                       "4" if pos_order_review.review_star == "star4" else
                       "5"),
            'rating_text': pos_order_review.review_text
        }
