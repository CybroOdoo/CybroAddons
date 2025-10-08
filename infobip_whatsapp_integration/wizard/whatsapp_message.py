# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Jabin MP (odoo@cybrosys.com)
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
from infobip_channels import WhatsAppChannel
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class WhatsAppMessage(models.TransientModel):
    """WhatsApp Message Wizard Model This model is used to send various types
     of WhatsApp messages."""
    _name = 'whatsapp.message'
    _description = 'WhatsApp Message Wizard'

    message_type = fields.Selection([
        ('text', 'Text Message'),
        ('button', 'Interactive Button  Message'),
        ('contact', 'Share Contact Details'),
        ('list', 'Interactive List  Message'),
        ('location', 'Share Location'),
    ], string='Message Type', default='text',
        help="Choose a method to send Message")
    text_message = fields.Char(string='Text Message',
                               help='Enter the text message content')
    partner_name = fields.Char(string='Partner Name',
                               readonly=True,
                               store=True, help='Name of the partner')
    partner_mobile = fields.Char(string='Partner Mobile',
                                 readonly=True,
                                 store=True,
                                 help='Mobile number of the partner')
    text = fields.Char(string="Type Header Text", help='Enter the header text')
    yes_text = fields.Char(string="Text for Yes Reply",
                           help='Text for the "Yes" reply option')
    no_text = fields.Char(string="Text for No Reply",
                          help='Text for the "No" reply option')
    later_text = fields.Char(string="Text for Later Reply",
                             help='Text for the "Later" reply option')
    partner_ids = fields.Many2many('res.partner', string='Select Partners',
                                   help='Select one or more partners')
    footer_text = fields.Char(string="Type Footer Text",
                              help='Enter the footer text')
    section_title = fields.Char(string="Title of Section",
                                help='Title of the section')
    section1_title = fields.Char(string="Type Option 1 Title",
                                 help='Title for Option 1')
    section1_description = fields.Char(string="Type Option 1 Description",
                                       help='Description for Option 1')
    section2_title = fields.Char(string="Type Option 2 Title",
                                 help='Title for Option 2')
    section2_description = fields.Char(string="Type Option 2 Description",
                                       help='Description for Option 2')
    section3_title = fields.Char(string="Type Option 3 Title",
                                 help='Title for Option 3')
    section3_description = fields.Char(string="Type Option 3 Description",
                                       help='Description for Option 3')
    section4_title = fields.Char(string="Type Option 4 Title",
                                 help='Title for Option 4')
    section4_description = fields.Char(string="Type Option 4 Description",
                                       help='Description for Option 4')

    def _get_config_parameter(self, param_name):
        """Retrieve a configuration parameter value from the database."""
        return self.env['ir.config_parameter'].sudo().get_param(param_name)

    def action_send_message(self):
        """Send a Text Message through WhatsApp."""
        url = self._get_config_parameter(
            'infobip_whatsapp_integration.base_url')
        api_key = self._get_config_parameter(
            'infobip_whatsapp_integration.api_key')
        number = self._get_config_parameter(
            'infobip_whatsapp_integration.infobip_whatsapp')
        if not all([url, api_key, number, self.text_message]):
            raise ValidationError(
                _('Incomplete Data: Please ensure you have provided all '
                  'necessary information to send the WhatsApp message.'))
        channel = WhatsAppChannel.from_auth_params({
            "base_url": url,
            "api_key": api_key, })
        response = channel.send_text_message({
            "from": number,
            "to": self.partner_mobile,
            "content": {
                "text": self.text_message
            }})
        return response

    def action_send_intractive_message(self):
        """Send an Interactive Button Message through WhatsApp."""
        url = self._get_config_parameter(
            'infobip_whatsapp_integration.base_url')
        api_key = self._get_config_parameter(
            'infobip_whatsapp_integration.api_key')
        number = self._get_config_parameter(
            'infobip_whatsapp_integration.infobip_whatsapp')
        if (self.text_message and self.partner_mobile and url and api_key and
                number and self.yes_text and self.no_text and self.later_text
                and self.text):
            channel = WhatsAppChannel.from_auth_params({
                "base_url": url,
                "api_key": api_key, })
            button_message = channel.send_interactive_buttons_message({
                "from": number,
                "to": self.partner_mobile,
                "content": {
                    "body": {
                        "text": self.text_message},
                    "action": {
                        "buttons": [
                            {
                                "type": "REPLY",
                                "id": "yes",
                                "title": self.yes_text
                            }, {
                                "type": "REPLY",
                                "id": "no",
                                "title": self.no_text
                            }, {
                                "type": "REPLY",
                                "id": "later",
                                "title": self.later_text
                            }, ]},
                    "header": {
                        "type": "TEXT",
                        "text": self.text
                    }}})
            return button_message
        else:
            raise ValidationError(
                _('Incomplete Data: Please ensure you have provided all'
                  ' necessary information to send the WhatsApp message.'))

    def action_send_contact_details(self):
        """ Share Contact Details through WhatsApp."""
        url = self._get_config_parameter(
            'infobip_whatsapp_integration.base_url')
        api_key = self._get_config_parameter(
            'infobip_whatsapp_integration.api_key')
        number = self._get_config_parameter(
            'infobip_whatsapp_integration.infobip_whatsapp')
        if (self.partner_ids and self.partner_mobile and url and api_key and
                number):
            channel = WhatsAppChannel.from_auth_params({
                "base_url": url,
                "api_key": api_key, })
            contact_messages = []
            for partner in self.partner_ids:
                contact = {
                    "addresses": [{
                        "street": partner.street,
                        "city": partner.city,
                        "zip": partner.zip,
                        "country": partner.country_id.name,
                        "type": "HOME"
                    }],
                    "emails": [{
                        "email": partner.email,
                        "type": "WORK"
                    }, ],
                    "name": {
                        "firstName": partner.name,
                        "formattedName": partner.name
                    },
                    "phones": [{
                        "phone": partner.phone,
                        "type": "HOME",
                    }, {
                        "phone": partner.mobile,
                        "type": "WORK",
                    }]}
                contact_messages.append(contact)
            for message in contact_messages:
                response = channel.send_contact_message({
                    "from": number,
                    "to": self.partner_mobile,
                    "content": {
                        "contacts": [message]
                    }})
            return response
        else:
            raise ValidationError(
                _('Incomplete Data: Please ensure you have provided all'
                  ' necessary information to send the WhatsApp message.'))

    def action_send_interactive_list_message(self):
        """Send an Interactive List Message through WhatsApp."""
        url = self._get_config_parameter(
            'infobip_whatsapp_integration.base_url')
        api_key = self._get_config_parameter(
            'infobip_whatsapp_integration.api_key')
        number = self._get_config_parameter(
            'infobip_whatsapp_integration.infobip_whatsapp')
        if (self.text_message and self.partner_mobile and url and api_key and
                number and self.text and self.footer_text and
                self.section_title and self.section1_title and
                self.section2_title and self.section3_title and
                self.section4_title and self.section1_description and
                self.section2_description and self.section3_description
                and self.section4_description):
            channel = WhatsAppChannel.from_auth_params({
                "base_url": url,
                "api_key": api_key, })
            list_message = channel.send_interactive_list_message({
                "from": number,
                "to": self.partner_mobile,
                "content": {
                    "body": {
                        "text": self.text_message
                    },
                    "action": {
                        "title": "See All Options",
                        "sections": [
                            {
                                "title": self.section_title,
                                "rows": [{
                                    "id": "1",
                                    "title": self.section1_title,
                                    "description": self.section1_description
                                }, {
                                    "id": "2",
                                    "title": self.section2_title,
                                    "description": self.section2_description
                                }, {
                                    "id": "3",
                                    "title": self.section3_title,
                                    "description": self.section3_description
                                }, {
                                    "id": "4",
                                    "title": self.section4_title,
                                    "description": self.section4_description
                                }]}]},
                    "header": {
                        "type": "TEXT",
                        "text": self.text},
                    "footer": {
                        "text": self.footer_text
                    }}})
            return list_message
        else:
            raise ValidationError(
                _('Incomplete Data: Please ensure you have provided all'
                  ' necessary information to send the WhatsApp message.'))

    def action_send_location_details(self):
        """Share Location Details through WhatsApp."""
        url = self._get_config_parameter(
            'infobip_whatsapp_integration.base_url')
        api_key = self._get_config_parameter(
            'infobip_whatsapp_integration.api_key')
        number = self._get_config_parameter(
            'infobip_whatsapp_integration.infobip_whatsapp')
        if (self.partner_ids and self.partner_mobile and url and api_key and
                number):
            for partner in self.partner_ids:
                channel = WhatsAppChannel.from_auth_params({
                    "base_url": url,
                    "api_key": api_key, })
                response = channel.send_location_message({
                    "from": number,
                    "to": self.partner_mobile,
                    "content": {
                        "latitude": partner.partner_latitude,
                        "longitude": partner.partner_longitude,
                        "name": partner.name,
                        "address": partner.street
                    }})
                return response
        else:
            raise ValidationError(
                _('Incomplete Data: Please ensure you have provided all'
                  ' necessary information to send the WhatsApp message.'))
