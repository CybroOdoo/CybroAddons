# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Arjun S (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class DashboardMail(models.TransientModel):
    """Creates the model dashboard.mail to sent the main from the dashboards"""
    _name = 'dashboard.mail'
    _description = 'Dashboard Mail'

    user_ids = fields.Many2many('res.users', string="Users",
                                domain="[('id','!=', uid)]",
                                help="Select User")
    base64code = fields.Char(string='Base 64', help='Base64 Code of the pdf')

    def action_send_mail(self):
        """Function for sending mail to the selected users"""
        for user in self.user_ids:
            mail_content = (
                           'Hi %s, <br/> '
                           'I hope this mail finds you well. I am pleased to share the <b>Dashboard Report</b> with you.<br/>'
                           'Please find the attachment<br/>') % user.name
            mail_values = {
                'subject': 'Dashboard Report',
                'author_id': self.env.user.partner_id.id,
                'body_html': mail_content,
                'email_to': user.email,
            }
            mail_id = self.env['mail.mail'].create(mail_values)
            attachment_values = {
                'name': 'Dashboard.pdf',
                'datas': self.base64code,
                'type': 'binary',
                'res_model': 'mail.mail',
                'res_id': mail_id.id,
            }
            attachment_id = self.env['ir.attachment'].create(attachment_values)
            mail_id.write({
                'attachment_ids': [(4, attachment_id.id)]
            })
            mail_id.send()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_cancel_mail(self):
        """Function for refreshing the page while clicking cancel"""
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
