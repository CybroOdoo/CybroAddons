# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_multi_confirm(self):
        """
        Confirm multiple sale orders.

        This method confirms sale orders in draft or sent state. It is intended
        to be used as a batch confirmation for multiple sale orders selected
        through the context.

        :return: None
        """
        for order in self.env['sale.order'].browse(
                self.env.context.get('active_ids')).filtered(
                lambda o: o.state in ['draft', 'sent']):
            order.action_confirm()

    def action_multi_cancel(self):
        """
        Cancel multiple sale orders with an additional check for the 'locked'
        status.

        This method cancels sale orders selected through the context, excluding
        those that are marked as 'locked'.
        It is intended to be used as a batch cancellation for multiple sale
        orders, with an option to disable cancellation warnings.

        :return: None
        """
        for order in self.env['sale.order'].browse(
                self.env.context.get('active_ids')).filtered(
                lambda o: not o.locked):
            order.with_context(disable_cancel_warning=True).action_cancel()
