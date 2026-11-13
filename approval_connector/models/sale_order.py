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


class SaleOrder(models.Model):
    """Class inherited for adding extra fields and methods"""
    _inherit = 'sale.order'

    state = fields.Selection(
        selection_add=[('approve', 'To Approve'), ('approved', 'Approved'),
                       ('sale',), ])
    is_approved = fields.Boolean(string='Approved', default=False,
                                 copy=False)

    def _can_be_confirmed(self):
        """This function is used to check the state of the order"""
        self.ensure_one()
        return self.state in {'draft', 'sent', 'approved'}

    def action_draft(self):
        """Reset the approval flag, so a re-drafted order is approved again"""
        res = super().action_draft()
        self.filtered(lambda order: order.state == 'draft').write(
            {'is_approved': False})
        return res

    def action_confirm(self):
        """Method is used to confirm the order"""
        approval = self.env['approval.category'].search([
            ('approval_type', '=', 'sale'),
            ('approver_ids', '!=', False),
        ], limit=1)
        to_approve = self.filtered(
            lambda order: approval and not order.is_approved)
        if to_approve:
            for order in to_approve:
                self.env['approval.request'].create({
                    'name': order.name,
                    'request_owner_id': (order.user_id or self.env.user).id,
                    'category_id': approval.id,
                    'date_start': fields.Datetime.now(),
                    'date_end': fields.Datetime.now(),
                    'order_id': order.id,
                }).action_confirm()
                order.message_post(
                    body=_("%(user)s created a request for approval for "
                           "%(order)s", user=self.env.user.name,
                           order=order.name),
                    message_type='comment'
                )
                order.write({'state': 'approve'})
            remaining = self - to_approve
            return remaining.action_confirm() if remaining else True
        # Core only confirms orders in draft or sent state
        self.write({'state': 'draft'})
        return super().action_confirm()
