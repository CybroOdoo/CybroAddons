# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    state = fields.Selection([('draft', 'Draft'), ('approve', 'Approved'),
                              ("cancel", "Cancelled")], default='draft', help='Status of the contact',
                             tracking=True)

    approver_id = fields.Many2one(
        'res.users', string="Approved By", readonly=True,  help='Person responsible for validating the contacts.')

    def action_approve_contact(self):
        """Manager validating the contacts."""
        if self.env.user.has_group(
                'odoo_contact_approval.group_contacts_approval'):
            self.write({
                'state': "approve",
                'approver_id': self.env.uid
            })
        else:
            raise UserError(_(
                "You do not have the access right to Contacts Approval."
                " Please contact your administrator.")
            )

    def action_cancel_contact(self):
        """Manager cancelling the contacts."""
        if self.env.user.has_group(
                'odoo_contact_approval.group_contacts_approval'):
            self.write({
                'state': "cancel",
                'approver_id': None
            })
        else:
            raise UserError(_(
                "You do not have the access right to Contacts Approval."
                " Please contact your administrator.")
            )

    def action_reset_contact(self):
        """Manager resetting the contacts."""
        if self.env.user.has_group(
                'odoo_contact_approval.group_contacts_approval'):
            self.write({
                'state': "draft",
                'approver_id': None
            })
        else:
            raise UserError(_(
                "You do not have the access right to Contacts Approval."
                " Please contact your administrator.")
            )
