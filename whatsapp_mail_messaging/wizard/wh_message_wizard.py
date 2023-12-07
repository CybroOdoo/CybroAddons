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


class WhatsappSendMessage(models.TransientModel):
    _name = 'whatsapp.message.wizard'

    partner_id = fields.Many2one('res.partner', string="Recipient")
    mobile = fields.Char(required=True, string="Contact Number")
    message = fields.Text(string="Message", required=True)
    message_name_id = fields.Many2one('selection.messages', string="Message Template")
    type_message = fields.Selection([('custom', 'Custom'), ('default', 'Default')], 'Message Type', default='custom')
    image_1920 = fields.Binary(readonly=1)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Function for fetching the mobile number and image of partner
        in Odoo"""
        self.mobile = self.partner_id.mobile
        self.image_1920 = self.partner_id.image_1920

    @api.onchange('message_name_id')
    def _onchange_type_message(self):
        """Function to set the default message based on type_message"""
        if self.message_name_id:
            self.message = self.message_name_id.message

    @api.onchange('type_message')
    def _onchange_type_message_type(self):
        """Function to set the default message based on type_message"""
        if self.type_message == 'default':
            self.message = self.message_name_id.message

    def send_message(self):
        """In this function we are redirecting to the whatsapp web
        with required parameters"""
        if self.message and self.mobile:
            message_string = ''
            message = self.message.split(' ')
            for msg in message:
                message_string = message_string + msg + '%20'
            message_string = message_string[:(len(message_string) - 3)]
            message_post_content = message_string
            if self.partner_id:
            	self.partner_id.message_post(body=message_post_content)
            return {
                'type': 'ir.actions.act_url',
                'url': "https://api.whatsapp.com/send?phone=" + self.mobile + "&text=" + message_string,
                'target': 'new',
                'res_id': self.id,
            }
