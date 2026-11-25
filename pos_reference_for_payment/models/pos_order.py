# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _process_payment_lines(self, pos_order, order, pos_session, draft):
        """Ensure that the payment reference is applied to all payment lines"""
        payment_reference = False
        ui_payment_lines = pos_order.get('payment_ids') or pos_order.get('statement_ids') or []
        for ui_paymentline in ui_payment_lines:
            if isinstance(ui_paymentline, (list, tuple)) and len(ui_paymentline) >= 3 and isinstance(ui_paymentline[2],
                                                                                                     dict):
                if ui_paymentline[2].get('user_payment_reference'):
                    payment_reference = ui_paymentline[2]['user_payment_reference']
                    break

        if payment_reference:
            for ui_paymentline in ui_payment_lines:
                if isinstance(ui_paymentline, (list, tuple)) and len(ui_paymentline) >= 3 and isinstance(
                        ui_paymentline[2], dict):
                    ui_paymentline[2]['user_payment_reference'] = payment_reference

        res = super()._process_payment_lines(pos_order, order, pos_session, draft)
        if payment_reference and order:
            order.payment_ids.filtered(lambda p: not p.user_payment_reference).write({
                'user_payment_reference': payment_reference
            })
        return res
