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
from odoo.exceptions import UserError


class GdprRequest(models.Model):
    """Request of a customer to download or delete their personal data."""
    _name = 'gdpr.request'
    _description = 'GDPR Request'
    _order = 'id desc'

    name = fields.Char(string='Reference', readonly=True, copy=False,
                       default='New', help='Reference of the request.')
    req_name = fields.Char(string='Name', help='Name of the request.')
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 required=True,
                                 help='Customer whose data is requested.')
    req_type = fields.Selection([
        ('download', 'Download Data'),
        ('delete', 'Delete Data')], string='Request Type', required=True,
        default='download', help='Download or delete the personal data.')
    state = fields.Selection([
        ('pending', 'Pending'),
        ('cancel', 'Cancelled'),
        ('done', 'Done')], default='pending', required=True,
        help='Status of the request.')
    template_id = fields.Many2one('gdpr.template',
                                  required=True,
                                  help='Template listing the requested data.')

    @api.model_create_multi
    def create(self, vals_list):
        """Give each request a reference from the sequence."""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'gdpr.request') or 'New'
        return super().create(vals_list)

    def _check_pending(self):
        """Only pending requests can be approved or cancelled."""
        if any(request.state != 'pending' for request in self):
            raise UserError(
                self.env._('Only pending requests can be processed.'))

    def action_confirm_request(self):
        """Approve download requests: the customer can download the PDF."""
        self._check_pending()
        if any(request.req_type != 'download' for request in self):
            raise UserError(
                self.env._('Use Wipe Data to approve a delete request.'))
        self.write({'state': 'done'})
        self._send_status_email()

    def action_delete_request(self):
        """Approve delete requests: clear the template fields of the
        customer."""
        self._check_pending()
        if any(request.req_type != 'delete' for request in self):
            raise UserError(
                self.env._('Use Confirm to approve a download request.'))
        self.check_access('write')
        # The email address may be one of the cleared fields
        emails = {request.id: request.partner_id.email for request in self}
        for request in self:
            field_names = request.template_id.sudo().field_ids.mapped('name')
            request.partner_id.sudo().write(dict.fromkeys(field_names, False))
        self.write({'state': 'done'})
        self._send_status_email(emails)

    def action_cancel_request(self):
        """Cancel the requests and inform the customers."""
        self._check_pending()
        self.write({'state': 'cancel'})
        self._send_status_email()

    def _send_status_email(self, emails=None):
        """Email the customers whose template allows messages. ``emails``
        gives the address to use per request, when the address of the
        customer has just been cleared."""
        mail_template = self.env.ref(
            'website_gdpr_odoo.gdpr_request_email_template')
        for request in self:
            email = (emails or {}).get(request.id) or request.partner_id.email
            if not request.template_id.allow_messages or not email:
                continue
            email_values = None
            if email != request.partner_id.email:
                email_values = {'email_to': email, 'recipient_ids': []}
            mail_template.send_mail(
                request.id, email_values=email_values,
                email_layout_xmlid='mail.mail_notification_light')

    def get_gdpr_data(self):
        """Return the label and the value of each template field of the
        customer, as shown in the PDF."""
        self.ensure_one()
        partner = self.partner_id.sudo()
        values = []
        for field in self.template_id.sudo().field_ids:
            value = partner[field.name]
            if field.ttype in ('many2one', 'many2many'):
                text = ', '.join(value.mapped('display_name'))
            elif field.ttype == 'boolean':
                text = self.env._('Yes') if value else self.env._('No')
            elif field.ttype == 'binary':
                text = self.env._('[Binary Data]') if value else ''
            elif field.ttype == 'selection':
                text = dict(partner._fields[field.name]._description_selection(
                    self.env)).get(value, '')
            else:
                text = str(value) if value not in (False, None) else ''
            values.append({
                'name': field.field_description or field.name,
                'data': text or self.env._('No data for this field'),
            })
        return values
