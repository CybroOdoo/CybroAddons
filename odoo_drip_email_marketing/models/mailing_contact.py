#############################################################################
#
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
#############################################################################
from odoo import api, fields, models


class MailingContact(models.Model):
    """Show the drip mails sent to the mailing contacts."""
    _inherit = 'mailing.contact'

    drip_history_ids = fields.One2many(
        'drip.mailing.history', 'contact_id')
    drip_count = fields.Integer(
        compute="_compute_drip_count",
        help="Number of drip mails sent")

    @api.model_create_multi
    def create(self, vals_list):
        """Send the subscription mail of the lists, also when they are
        joined through the many2many field, which does not create the
        subscriptions through their model."""
        records = super(
            MailingContact, self.with_context(drip_subscription_mail_pending=True),
        ).create(vals_list)
        # The many2many shares the subscription table: read it again
        records.invalidate_recordset(['subscription_ids'])
        records.subscription_ids._send_drip_subscription_mail()
        return records.with_env(self.env)

    def write(self, vals):
        """Send the subscription mail of the lists joined by this write."""
        if not {'list_ids', 'subscription_ids'} & vals.keys():
            return super().write(vals)
        subscriptions = self.subscription_ids
        res = super(
            MailingContact, self.with_context(drip_subscription_mail_pending=True),
        ).write(vals)
        self.invalidate_recordset(['subscription_ids'])
        (self.subscription_ids - subscriptions)._send_drip_subscription_mail()
        return res

    @api.depends('drip_history_ids')
    def _compute_drip_count(self):
        """Count the drip mails sent to the contact."""
        for contact in self:
            contact.drip_count = len(contact.drip_history_ids)

    def get_drip_history(self):
        """Open the drip mails sent to the contact."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._("Drip History"),
            'view_mode': 'list,form',
            'res_model': 'drip.mailing.history',
            'domain': [('contact_id', '=', self.id)],
            'context': {'create': False},
        }
