# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields, api
import requests
import json
from odoo.exceptions import UserError


class SystrayIcon(models.TransientModel):
    _name = 'help.icons'
    _description = 'Help Icon'

    name = fields.Char(string='Name', required='True')
    email = fields.Char(string='Email', required='True')
    description = fields.Text(string='Description', required='True')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    t_type = fields.Selection([
        ('functional', 'Functional Support'),
        ('technical', 'Technical Support'), ], string="Support Type", default="technical")

    def whatsapp_button(self):
        if self.description and self.name:
            message_string = ''
            message = self.description.split(' ')
            for msg in message:
                message_string = message_string + msg + '%20'
            message_string = message_string[:(len(message_string) - 3)]
            phone_number = str(+918606827707)
            print("https://api.whatsapp.com/send?phone=" + phone_number + "&text=" + message_string)
            close_wizard = {'type': 'ir.actions.act_window_close'}

            url_open = {
                'type': 'ir.actions.act_url',
                'url': "https://api.whatsapp.com/send?phone=" + phone_number + "&text=" + message_string,
                'target': 'new',
                'res_id': self.id,
                'tag': 'reload',
            }
            return url_open

    def confirm_button(self):
        body = {
            'name': self.name,
            'email': self.email,
            'description': self.description,
            't_type': self.t_type,
            'attachments': [(str(rec.datas), rec.name) for rec in self.attachment_ids],
        }
        print(body)
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        response = requests.post(url='https://api.cybrosys.us/help/request', json=body,
                                 headers=headers, data=json.dumps(body))

        if response.status_code == 200:
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'Request Created Successfully',
                    'type': 'rainbow_man',
                    'img_url': '/cybrosys_support_client/static/src/images/test.jpeg',
                    'target': 'new',
                }
            }

        else:
            raise UserError('Failed')

    def success_msg(self):
        return {
            'name': 'Message',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'custom.pop.message',
            'target': 'new',
            'context': {'default_name': "Successfully Submitted."}
        }


class CustomPopMessage(models.TransientModel):
    _name = "custom.pop.message"

    name = fields.Char('Message')
