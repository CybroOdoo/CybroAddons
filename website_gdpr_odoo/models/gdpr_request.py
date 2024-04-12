# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
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
################################################################################
import base64
from odoo import api, fields, models


class GDPRRequest(models.Model):
    """
    The GDPRRequest class fields and different methods  are included.
        Methods:
            action_confirm_request(self):
                For action confirm button change state to confirm.
            action_delete_request(self,**kw):
               For updating the values in 'res.partner'(deleting records).
            action_cancel_request(self):
                For action cancel button change state to cancel.
            action_download_pdf(self):
                For downloading the selected data.
            create(self):
                For getting overriding sequence number.
    """
    _name = "gdpr.request"
    _description = "GDPR Request"

    name = fields.Char(string="Serial Number", readonly=True,
                       copy=False, default='New', help="The serial number")
    req_name = fields.Char(string="Name", help="Request Name")
    partner_id = fields.Many2one('res.partner', string="Customer",
                                 help="Specify the customer for the request.")
    req_type = fields.Selection([
        ('download', 'Download Data'),
        ('delete', 'Delete Data')], string="Request Type",
        help="Please specify the type of request you want to make.")
    state = fields.Selection([
        ('pending', 'Pending'),
        ('cancel', 'Cancel'),
        ('done', 'Done')], default="pending", help="State of the request")
    template_id = fields.Many2one('gdpr.template', string="Template",
                                  help="Selected Template")

    def action_confirm_request(self):
        """
        Summary:
            For action confirm
        """
        self.write({'state': 'done'})
        self.action_send_email()

    def action_send_email(self):
        """
        Summary:
            For sending mail to the partner when the request is confirmed or
            canceled
        """
        state = "Confirmed" if self.state == "done" else "Cancelled"
        email_values = {
            'email_to': self.partner_id.email,
            'content': "Your Gdpr Request " + self.name + " for " +
                       self.req_type + " data is " + state,
            'company': self.env.company.name,
        }
        mail_template = self.env.ref(
            'website_gdpr_odoo.gdpr_request_email_template')
        mail_template.with_context(email_values).send_mail(self.id,
                                                           email_layout_xmlid='mail.mail_notification_light',
                                                           force_send=True)

    def action_delete_request(self):
        """
        Summary:
            For updating the values in 'res.partner'(deleting records)
        """
        value_list = [partner_field.name for partner_field in
                      self.template_id.field_ids]
        for value in value_list:
            self.partner_id.write({
                value: False,
            })
        self.write({'state': 'done'})

    def action_cancel_request(self):
        """
        Summary:
            For action cancel
        """
        self.write({'state': 'cancel'})
        self.action_send_email()

    def action_download_pdf(self, data):
        """
        Summary:
            For downloading the selected data
        """
        value_list = []
        request_id = self.env['gdpr.request'].sudo().browse(data)
        partner_fields = request_id.template_id.sudo().field_ids
        partner_id = request_id.partner_id
        for rec in partner_fields:
            if rec.ttype == "many2one":
                field_val = partner_id.mapped(rec.name).name
                if field_val:
                    list_to_str = ' '.join([str(elem) for elem in field_val])
                else:
                    list_to_str = False
                value_list.append({'data': list_to_str,
                                   'name': rec.field_description})
            else:
                field_val = partner_id.mapped(rec.name)
                list_to_str = ' '.join([str(elem) for elem in field_val])
                value_list.append({'data': list_to_str,
                                   'name': rec.field_description})
        values = {
            'name': partner_id.name,
            'value': value_list
        }
        pdf = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'website_gdpr_odoo.action_pdf_download', request_id.id, data=values)
        attachment = self.env['ir.attachment'].sudo().create({
            'datas': base64.b64encode(pdf[0]),
            'name': "Data Download",
            'type': 'binary',
            'res_model': 'gdpr.request',
            'res_id': request_id.id,
            'public': True
        })
        return {
            'url': f'/web/content/{attachment.id}?download=true&amp;access_token=',
        }

    @api.model
    def create(self, vals):
        """
        Summary:
            For getting overriding sequence number
        """
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'request.sequence') or 'New'
        return super(GDPRRequest, self).create(vals)
