# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class IrAttachment(models.Model):
    """ Added document expiry information"""
    _inherit = 'ir.attachment'

    expiry_date = fields.Date(string='Expiry Date',
                              help="for setting expiry date for the document")
    expiry_notification = fields.Boolean(string='Expiry Date Notification',
                                         help="For sending expiry notification")
    partner_id = fields.Many2one('res.partner', string="partner",
                                 help="For adding the partner ")
    document_email_to = fields.Char(
        default=lambda self: self.env['ir.config_parameter'].sudo().get_param(
            'res.config.settings.email'), string="Email to",
        help="For getting owner email")
    document_mai_customer = fields.Boolean(
        default=lambda self: self.env['ir.config_parameter'].sudo().get_param(
            'res.config.settings.notify_customer'), string="Email to customer",
        help="Notify email to customer ")

    def document_expire_notification(self):
        """ Automatically sent email when the
                document expiration date is over"""
        if self.env['ir.config_parameter'].sudo().get_param(
                'res.config.settings.notify_customer'):
            attachments = self.search([('expiry_date', '!=', None)])
            for attachment in attachments:
                if attachment.expiry_date < fields.Date.today():
                    mail_template = attachment.env.ref(
                        'advanced_project_management_system.document_expire_notification_to_customer')
                    mail_template.send_mail(attachment.id, force_send=True)
        attachments = self.search([('expiry_date', '!=', None)])
        for attachment in attachments:
            if attachment.expiry_notification:
                if attachment.expiry_date < fields.Date.today():
                    mail_template = attachment.env.ref(
                        'advanced_project_management_system.document_expire_notification_mail_template')
                    mail_template.send_mail(attachment.id, force_send=True)

    @api.onchange('res_id')
    def _onchange_res_id(self):
        """ Compute customer name and add to attachment from projects"""
        attachments = self.search([('res_model', '=', 'project.project')])
        for attachment in attachments:
            projects = self.env['project.project'].search(
                [('id', '=', attachment.res_id)])
            if projects.partner_id:
                attachment.partner_id = projects.partner_id.id
