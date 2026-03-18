# -- coding: utf-8 --
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _


class SendFollowupWizard(models.TransientModel):
    """
    Send Follow-up Communication Wizard
    """
    _name = 'send.followup.wizard'
    _description = 'Send Follow-up Communication Wizard'

    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    risk_score_id = fields.Many2one('payment.risk.score', string='Risk Score')
    subject = fields.Char(
        string='Subject',
        default=lambda self: _('Payment Follow-up Reminder'))
    message = fields.Html(string='Message', required=True)
    send_email = fields.Boolean(string='Send Email', default=True)
    send_sms = fields.Boolean(string='Send SMS', default=False)
    attach_statement = fields.Boolean(
        string='Attach Statement of Account', default=False)
    overdue_invoices = fields.Many2many(
        'account.move', string='Overdue Invoices',
        compute='_compute_overdue_invoices')

    @api.depends('partner_id')
    def _compute_overdue_invoices(self):
        """
        Compute the overdue invoices for the selected partner.
        """
        today = fields.Date.today()
        for rec in self:
            if rec.partner_id:
                rec.overdue_invoices = self.env['account.move'].search([
                    ('partner_id', '=', rec.partner_id.id),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                    ('payment_state', 'not in', ('paid', 'in_payment')),
                    ('invoice_date_due', '<', today),
                ])
            else:
                rec.overdue_invoices = False

    @api.onchange('risk_score_id')
    def _onchange_risk_score(self):
        """
        Update the message field based on the selected risk score suggestion.
        """
        if self.risk_score_id and self.risk_score_id.followup_suggestion:
            self.message = '<p>%s</p>' % self.risk_score_id.followup_suggestion.replace('\n', '<br/>')

    def action_send(self):
        """
        Send the follow-up email to the partner and log the message in the partner chatter.
        """
        self.ensure_one()
        partner = self.partner_id
        if self.send_email and partner.email:
            template_values = {
                'subject': self.subject,
                'body_html': self.message,
                'email_to': partner.email,
                'email_from': self.env.user.email or self.env.company.email,
                'partner_ids': [(4, partner.id)],
            }
            mail = self.env['mail.mail'].create(template_values)
            mail.send()
        # Log a note on the partner chatter
        partner.message_post(
            body=self.message,
            subject=self.subject,
            message_type='email',
            subtype_xmlid='mail.mt_comment',
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Follow-up Sent'),
                'message': _('Follow-up communication sent to %s.') % partner.name,
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
