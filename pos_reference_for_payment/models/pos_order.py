# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _process_payment_lines(self, pos_order, order, pos_session, draft):
        """Ensure that the payment reference is applied to all payment lines"""
        payment_reference = False
        ui_payment_lines = pos_order.get('payment_ids') or pos_order.get('statement_ids') or []
        for ui_paymentline in ui_payment_lines:
            if ui_paymentline[2].get('user_payment_reference'):
                payment_reference = ui_paymentline[2]['user_payment_reference']
                break
        
        if payment_reference:
            for ui_paymentline in ui_payment_lines:
                ui_paymentline[2]['user_payment_reference'] = payment_reference

        return super(PosOrder, self)._process_payment_lines(pos_order, order, pos_session, draft)

    def _payment_fields(self, order, ui_paymentline):
        """Overridden to include user_payment_reference in payment fields"""
        res = super(PosOrder, self)._payment_fields(order, ui_paymentline)
        res['user_payment_reference'] = ui_paymentline.get('user_payment_reference')
        return res
