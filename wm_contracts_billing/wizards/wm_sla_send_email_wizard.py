# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class WmSlaSendEmailWizard(models.TransientModel):
    """Wizard to compose and dispatch SLA breach notification emails to contract contacts."""
    _name = 'wm.sla.send.email.wizard'
    _description = 'SLA Send Email Wizard'

    sla_id = fields.Many2one('wm.sla', string='SLA', required=True)
    contract_id = fields.Many2one('wm.partner.contract', string='Contract', required=True)
    reason = fields.Text(string='Reason', required=True)

    def action_send_email(self):
        """
        Send the breach email using the configured template, and log the
        message in chatter.
        """
        self.ensure_one()
        if not self.sla_id.breach_template_id:
            raise ValidationError(_("Please configure a Breach Notification Template on the SLA before sending."))
        if not self.contract_id:
            raise ValidationError(_("Please select a Contract to send the email to."))

        partner = self.contract_id.partner_id
        if not partner.email:
            raise ValidationError(_("The customer %(partner_name)s does not have an email address configured.", partner_name=partner.name))

        email_values = {
            'email_to': partner.email,
            'recipient_ids': [(4, partner.id)],
        }
        self.sla_id.breach_template_id.with_context(reason=self.reason).send_mail(
            self.contract_id.id, force_send=True, email_values=email_values
        )

        message_body = _(
            "SLA Breach Email sent to %(partner_name)s (Contract: %(contract_name)s) for SLA %(sla_name)s. Reason: %(reason)s",
            partner_name=partner.name,
            contract_name=self.contract_id.name,
            sla_name=self.sla_id.name,
            reason=self.reason,
        )

        self.sla_id.message_post(body=message_body)
        self.contract_id.message_post(body=message_body)
