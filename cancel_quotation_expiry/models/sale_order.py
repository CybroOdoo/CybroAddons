# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Cybrosys Technologies (odoo@cybrosys.com)
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
###############################################################################
from datetime import date
from odoo import models


class SaleOrder(models.Model):
    """Inherit Sale Order to add functionality for canceling expired
    quotations."""
    _inherit = 'sale.order'

    def cancel_expired_quotation(self):
        """Automatically cancel expired quotations and send mail."""
        orders = self.search([
            ('state', 'in', ['draft', 'sent']),
            ('validity_date', '!=', False),
            ('validity_date', '<', date.today()),
        ])

        template = self.env.ref(
            'sale.mail_template_sale_cancellation',
            raise_if_not_found=False
        )

        for order in orders:
            # Send cancellation email (optional)
            if template:
                template.send_mail(
                    order.id,
                    force_send=True,
                    raise_exception=False
                )
            # Cancel the quotation
            order._action_cancel()
