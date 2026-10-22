# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, models


class PosPayment(models.Model):
    """Get payment details of pos session"""
    _inherit = 'pos.payment'

    @api.model
    def get_payment_summary(self, order_ids):
        """Function to get payment details"""
        payments_summary = []
        if order_ids:
            self.env.cr.execute("""
                SELECT method.name, method.id, sum(payment.amount) AS total
                FROM pos_payment AS payment
                INNER JOIN pos_payment_method AS method ON payment.payment_method_id = method.id
                WHERE payment.pos_order_id IN %s
                GROUP BY method.name, method.id
            """, (tuple(order_ids),))
            for row in self.env.cr.dictfetchall():
                name = row['name']
                if isinstance(name, dict):
                    name = name.get(self.env.lang) or name.get('en_US') or next(iter(name.values()), '')
                row['name'] = name
                payments_summary.append(row)
        return payments_summary
