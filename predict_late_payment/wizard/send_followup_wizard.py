# -*- coding: utf-8 -*-
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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import base64
import logging
import re
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


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
        Update the message field based on the selected risk score communication draft.
        Prefers the drafted followup_email, falling back to followup_suggestion.
        """
        if self.risk_score_id:
            text = self.risk_score_id.followup_email or self.risk_score_id.followup_suggestion or ''
            if text:
                self.message = '<p>%s</p>' % text.replace('\n', '<br/>')

    def _generate_statement_html(self, partner):
        """Generate HTML statement of account for customer."""
        company = self.env.company
        currency = company.currency_id.symbol or company.currency_id.name or ''
        today = fields.Date.today()
        invoices = self.overdue_invoices or self.env['account.move'].search([
            ('partner_id', '=', partner.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'not in', ('paid', 'in_payment')),
        ])
        rows = []
        total_due = 0.0
        for inv in invoices:
            total_due += inv.amount_residual
            rows.append(f"""
                <tr>
                    <td style="padding:8px;border:1px solid #ddd;">{inv.name}</td>
                    <td style="padding:8px;border:1px solid #ddd;">{inv.invoice_date or ''}</td>
                    <td style="padding:8px;border:1px solid #ddd;">{inv.invoice_date_due or ''}</td>
                    <td style="padding:8px;border:1px solid #ddd;text-align:right;">{currency} {inv.amount_total:,.2f}</td>
                    <td style="padding:8px;border:1px solid #ddd;text-align:right;color:#c00;">{currency} {inv.amount_residual:,.2f}</td>
                </tr>
            """)
        table_rows = "".join(rows) if rows else "<tr><td colspan='5' style='padding:8px;text-align:center;'>No open invoices found.</td></tr>"
        return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/><title>Statement of Account - {partner.name}</title></head>
<body style="font-family:Arial,sans-serif;margin:20px;color:#333;">
    <div style="border-bottom:2px solid #b12126;padding-bottom:10px;margin-bottom:20px;">
        <h2 style="margin:0;color:#b12126;">{company.name}</h2>
        <div style="font-size:12px;color:#666;">{company.email or ''} | {company.phone or ''}</div>
    </div>
    <h3>Statement of Account</h3>
    <p><strong>Customer:</strong> {partner.name}<br/>
    <strong>Date:</strong> {today}<br/>
    <strong>Total Outstanding Balance:</strong> <span style="color:#c00;font-weight:bold;">{currency} {total_due:,.2f}</span></p>
    <table style="width:100%;border-collapse:collapse;margin-top:15px;font-size:13px;">
        <thead>
            <tr style="background:#f5f5f5;">
                <th style="padding:8px;border:1px solid #ddd;text-align:left;">Invoice</th>
                <th style="padding:8px;border:1px solid #ddd;text-align:left;">Date</th>
                <th style="padding:8px;border:1px solid #ddd;text-align:left;">Due Date</th>
                <th style="padding:8px;border:1px solid #ddd;text-align:right;">Total</th>
                <th style="padding:8px;border:1px solid #ddd;text-align:right;">Amount Due</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
    <p style="margin-top:25px;font-size:12px;color:#666;">Please arrange for payment at your earliest convenience.</p>
</body>
</html>"""

    def action_send(self):
        """
        Send the follow-up email and/or SMS to the partner and log the message in chatter.
        """
        self.ensure_one()
        partner = self.partner_id
        attachment_ids = []

        if self.attach_statement:
            statement_html = self._generate_statement_html(partner)
            statement_att = self.env['ir.attachment'].create({
                'name': f"Statement_of_Account_{partner.name.replace(' ', '_')}_{fields.Date.today()}.html",
                'type': 'binary',
                'raw': statement_html.encode('utf-8'),
                'mimetype': 'text/html',
                'res_model': 'res.partner',
                'res_id': partner.id,
            })
            attachment_ids.append(statement_att.id)

        if self.send_email and partner.email:
            template_values = {
                'subject': self.subject,
                'body_html': self.message,
                'email_to': partner.email,
                'email_from': self.env.user.email or self.env.company.email,
                'partner_ids': [(4, partner.id)],
                'attachment_ids': [(6, 0, attachment_ids)] if attachment_ids else [],
            }
            mail = self.env['mail.mail'].create(template_values)
            mail.send()

        if self.send_sms:
            phone = getattr(partner, 'mobile', False) or partner.phone
            plain_body = re.sub(r'<[^>]+>', '', self.message or '').strip()
            if phone:
                sms_installed = 'sms.sms' in self.env
                if sms_installed:
                    try:
                        sms = self.env['sms.sms'].sudo().create({
                            'number': phone,
                            'body': plain_body[:160],
                            'partner_id': partner.id,
                        })
                        sms.send()
                    except Exception as e:
                        _logger.warning("Could not send SMS to %s: %s", phone, e)
                partner.message_post(
                    body=_("SMS Follow-up sent to %s:\n%s") % (phone, plain_body[:160]),
                    message_type='sms' if sms_installed else 'notification',
                    subtype_xmlid='mail.mt_note',
                )
            else:
                _logger.warning("No phone/mobile found for partner %s to send SMS.", partner.name)

        # Log on the partner chatter
        partner.message_post(
            body=self.message,
            subject=self.subject,
            message_type='email',
            subtype_xmlid='mail.mt_comment',
            attachment_ids=attachment_ids,
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
