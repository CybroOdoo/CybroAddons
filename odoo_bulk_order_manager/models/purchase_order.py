# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Gayathri V(odoo@cybrosys.com)
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
from odoo import models, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    """
    Inherits the model Purchase Order and extends to add the extra
    functionalities for the working of the app.
    """
    _inherit = 'purchase.order'

    def action_confirm_purchase_orders(self):
        """
        Method action_confirm_purchase_orders to confirm the purchase orders in
        the RFQ state from list view itself.
        """
        if all(item in ("draft", "sent") for item in self.mapped('state')):
            return {
                'name': 'Confirm Purchase Orders',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mass.order.confirmation',
                'target': 'new',
                'context': {
                    'default_purchase_order_ids': self.mapped('id'),
                    'default_is_purchase_order': True
                }
            }
        raise ValidationError(_(
            "Every Purchase Order needs to be in RFQ State or RFQ Sent State"))
