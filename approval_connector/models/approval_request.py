# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vishnu K P (<https://www.cybrosys.com>)
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
from odoo import fields, models, _


class ApprovalCategory(models.Model):
    _inherit = 'approval.request'

    """Class inherit for the approval request button in the form"""

    order_id = fields.Many2one('sale.order', string='Document',
                               help="Connection id for the sale order")

    def action_approve(self):
        """This method is used to confirm the order Approval"""
        res = super().action_approve()
        for order in [self.order_id]:
            approve_status = self.approver_ids.mapped('status')
            if all(status == 'approved' for status in approve_status) and order:
                order.write({'state': 'approved', 'is_approved': True})
                order.message_post(
                    body=_('Requested approval is Confirmed'),
                    message_type='comment')
        return res

    def action_refuse(self):
        """This method is used to reject the approval request"""
        res = super().action_refuse()
        if self.order_id:
            self.order_id._action_cancel()
        return res
