# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
# ############################################################################

from odoo import fields, models

class CustodyTransferEvent(models.Model):
    """
    Audit trail entries for a custody transfer.

    Every meaningful change (approval, state transition, quantity edit,
    manual override, dispute) is recorded here so the transfer can be
    reconstructed post-hoc. Events are immutable to non-admin users; admins
    can correct them but the original chatter on the transfer keeps the
    canonical history.
    """
    _name = "custody.transfer.event"
    _description = "Custody Transfer Event"
    _order = "event_date desc, id desc"

    transfer_id = fields.Many2one(
        "custody.transfer",
        string="Transfer",
        required=True,
        ondelete="cascade",
        index=True,
        help="Custody transfer this event belongs to.",
    )
    event_type = fields.Selection(
        [
            ("create", "Created"),
            ("state_change", "State Change"),
            ("approval", "Approval"),
            ("quantity_change", "Quantity Change"),
            ("dispute", "Dispute"),
            ("dispute_resolved", "Dispute Resolved"),
            ("override", "Manual Override"),
            ("note", "Note"),
        ],
        string="Event Type",
        required=True,
        help="Category of change recorded by this audit entry.",
    )
    event_date = fields.Datetime(
        string="Event Date",
        required=True,
        default=fields.Datetime.now,
        help="When the event was recorded.",
    )
    user_id = fields.Many2one(
        "res.users",
        string="User",
        required=True,
        default=lambda self: self.env.user,
        help="User responsible for the recorded event.",
    )
    description = fields.Text(
        string="Description",
        help="Human-readable explanation of what changed.",
    )
    old_value = fields.Char(
        string="Old Value",
        help="Previous value when the event represents a change.",
    )
    new_value = fields.Char(
        string="New Value",
        help="Updated value when the event represents a change.",
    )
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, help="The company managing this operational record or transaction.")
