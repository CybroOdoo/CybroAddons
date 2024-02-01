# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Jumana Jabin MP(<https://www.cybrosys.com>)
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


class PurchaseOrder(models.Model):
    """ Inherits the purchase_order model to add additional actions for
     multiple confirmation and cancellation. """
    _inherit = 'purchase.order'

    def action_multi_confirm(self):
        """Action method to confirm multiple purchase orders."""
        for order in self.env['purchase.order'].browse(
                self.env.context.get('active_ids')).filtered(
            lambda o: o.state in ['draft', 'sent']):
            order.button_confirm()

    def action_multi_cancel(self):
        """Action method to cancel multiple purchase orders."""
        for order in self.env['purchase.order'].browse(
                self.env.context.get('active_ids')):
            order.button_cancel()
