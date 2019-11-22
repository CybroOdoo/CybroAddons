# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sayooj A O(<https://www.cybrosys.com>)
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

from functools import partial

from odoo import models, api, fields


class OrderNotes(models.Model):
    """In this class pos.order is inherited for adding the waiter
    reference in the order and function for fetching the waiter
    from pos to backend order"""

    _inherit = 'pos.order'

    employee_id = fields.Many2one('hr.employee', string='Waiter')

    @api.model
    def _order_fields(self, ui_order):
        """In this function the waiter that we defined from the
        pos interface is fetched to the pos order which is created
        in the backend"""

        process_line = partial(self.env['pos.order.line']._order_line_fields,
                               session_id=ui_order['pos_session_id'])
        return {
            'name': ui_order['name'],
            'user_id': ui_order['user_id'] or False,
            'session_id': ui_order['pos_session_id'],
            'lines': [process_line(l) for l in ui_order['lines']] if ui_order['lines'] else False,
            'pos_reference': ui_order['name'],
            'partner_id': ui_order['partner_id'] or False,
            'date_order': ui_order['creation_date'],
            'fiscal_position_id': ui_order['fiscal_position_id'],
            'pricelist_id': ui_order['pricelist_id'],
            'amount_paid': ui_order['amount_paid'],
            'amount_total': ui_order['amount_total'],
            'amount_tax': ui_order['amount_tax'],
            'amount_return': ui_order['amount_return'],
            'employee_id': ui_order.get('employee_id')

        }
