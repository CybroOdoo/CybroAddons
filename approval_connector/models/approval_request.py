# -*- coding: utf-8 -*-
######################################################################################
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: VISHNU KP (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################
from odoo import fields, models, _


class ApprovalRequest(models.Model):
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
