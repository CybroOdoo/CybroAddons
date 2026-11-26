# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models


class FollowupLine(models.Model):
    """A step of a reminder plan: how many days past the due date it
    applies and what it does (email, letter)."""
    _name = 'followup.line'
    _description = 'Follow-up Step'
    _order = 'delay'

    name = fields.Char(string="Step", required=True, translate=True,
                       help="Shown on the customer's follow-up, e.g. \"Second reminder\".")
    sequence = fields.Integer(help="Order of the step in lists.")
    delay = fields.Integer(string="Days Overdue", required=True,
                           help="Days after the invoice due date when this step starts; "
                                "a negative number reminds before the due date.")
    followup_id = fields.Many2one('account.followup', string="Reminder Plan",
                                  ondelete="cascade")
    send_email = fields.Boolean(
        string='Send an Email', default=True,
        help="When reached, email the reminder to the customer.")
    email_template_id = fields.Many2one(
        'mail.template', string='Email Template',
        domain=[('model', '=', 'res.partner')],
        help="Template used for the reminder email. Falls back to the default "
             "follow-up template when empty.")
    print_letter = fields.Boolean(
        string='Print a Letter',
        help="Offer a printable reminder letter (PDF) at this level.")
