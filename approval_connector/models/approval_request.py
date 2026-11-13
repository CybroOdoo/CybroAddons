# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import fields, models, _


class ApprovalRequest(models.Model):
    """Class inherit for the approval request button in the form"""
    _inherit = 'approval.request'

    order_id = fields.Many2one('sale.order', string='Document',
                               help="Connection id for the sale order")

    def action_approve(self, approver=None):
        """This method is used to confirm the order Approval"""
        res = super().action_approve(approver)
        for request in self:
            order = request.order_id
            approve_status = request.approver_ids.mapped('status')
            if order and all(status == 'approved'
                             for status in approve_status):
                order.write({'state': 'approved', 'is_approved': True})
                order.message_post(
                    body=_('Requested approval is Confirmed'),
                    message_type='comment')
        return res

    def action_refuse(self, approver=None):
        """This method is used to reject the approval request"""
        res = super().action_refuse(approver)
        orders = self.mapped('order_id')
        if orders:
            orders._action_cancel()
        return res
