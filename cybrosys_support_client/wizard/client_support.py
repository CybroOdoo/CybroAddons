# -*- coding: utf-8 -*-
##############################################################################
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
##############################################################################
import base64
import requests
from odoo import fields, models
from odoo.exceptions import ValidationError


class ClientSupport(models.TransientModel):
    _name = 'client.support'
    _description = 'Client Support'

    name = fields.Char(string='Name', required='True', help='Enter name')
    email = fields.Char(string='Email', required='True',
                        help='Enter your Email')
    description = fields.Text(string='Description', required='True',
                              help='Specify your problem in detail.')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments',
                                      help='Attach files related to your problem.')
    support_type = fields.Selection([
        ('functional', 'Functional Support'),
        ('technical', 'Technical Support'), ], string="Support Type",
        required='True', default="technical", help='Select support type')

    def confirm_button(self):
        """ Function for submitting the ticket """
        headers = {'Content-type': 'application/json'}
        response = requests.post(
            url='https://support.cybrosys.com/help/request',
            json={
                'params': {
                    'customer_name': self.name,
                    'email': self.email,
                    'description': self.description,
                    'support_type': self.support_type,
                    'attachments': [
                        {
                            'data': base64.b64encode(rec.datas).decode('utf-8'),
                            'name': rec.name
                        } for rec in self.attachment_ids
                    ],
                }
            },
            headers=headers)
        response_status = response.json()
        if response_status['result']['message'] == 'success':
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'Ticket Created Successfully',
                    'type': 'rainbow_man',
                    'target': 'new',
                }
            }
        else:
            raise ValidationError(
                "The ticket submission did not go through. Please try again.")

    def whatsapp_button(self):
        """ Function for getting support through Whatsapp"""
        if self.description and self.name:
            message_string = ''
            message = self.description.split(' ')
            for msg in message:
                message_string = message_string + msg + '%20'
            message_string = message_string[:(len(message_string) - 3)]
            phone_number = str(+918606827707)
            return {
                'type': 'ir.actions.act_url',
                'url': "https://wa.me/" + phone_number + "?text=" + message_string,
                'target': 'new',
                'res_id': self.id,
                'tag': 'reload',
            }
