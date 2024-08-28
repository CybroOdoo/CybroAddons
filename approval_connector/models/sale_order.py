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


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    """Class inherited for adding extra fields and methods"""

    state = fields.Selection(
        selection_add=[('approve', 'To Approve'), ('approved', 'Approved'),
                       ('sale',), ], string='State')
    is_approved = fields.Boolean(string='Approved', default=False,
                                 help='To check whether the order is approved')

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
