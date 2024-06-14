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


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    """Class inherited for adding extra fields and methods"""
    state = fields.Selection(
        selection_add=[('approve', 'To Approve'), ('approved', 'Approved'),
                       ('sale',), ])
    is_approved = fields.Boolean(string='Approved', default=False)

    def _can_be_confirmed(self):
        """This function is used to check the state of the order"""
        self.ensure_one()
        return self.state in {'draft', 'sent', 'approved'}

    def action_confirm(self):
        """Method is used to confirm the order"""
        approval = self.env['approval.category'].search(
            [('approval_type', '=', 'sale')])
        if approval and not self.is_approved:
            self.env['approval.request'].create({
                'name': self.name,
                'request_owner_id': self.user_id.id,
                'category_id': approval.id,
                'date_start': fields.Datetime.now(),
                'date_end': fields.Datetime.now(),
                'order_id': self.id,
            }).action_confirm()
            self.message_post(body=self.env.user.name + _(
                ' Created a request for approval for ') + self.name,
                              message_type='comment')
            self.write({'state': 'approve'})
        else:
            return super().action_confirm()
