# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#
#############################################################################
from os import remove
from openai import OpenAI
from odoo import api, models


class ChatGPTOdoo(models.Model):
    _name = 'open.chatgpt'
    _description = 'Open ChatGPT'

    @api.model
    def get_response(self, message):
        """Function for getting response based on the message."""
        api_key = self.env['ir.config_parameter'].sudo().get_param('chatgpt_odoo_connector.api_key')
        client = OpenAI(api_key=api_key)
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": message,
                    }
                ],
                model="gpt-3.5-turbo",
            )
        except Exception as e:
            message = str(e).split("'message':")[1]
            error_message = message.split(", 'type':")[0]
            return error_message
        return chat_completion.choices[0].message.content

    @api.model
    def edit_content(self, message, message_type):
        """Function for editing(shortening, lengthening, and rephrasing) the description """
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'chatgpt_odoo_connector.api_key')
        client = OpenAI(api_key=api_key)
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": f"{message_type}: {message}",
                    }
                ],
                model="gpt-3.5-turbo",
            )
        except Exception as e:
            message = str(e).split("'message':")[1]
            error_message = message.split(", 'type':")[0]
            return error_message
        return chat_completion.choices[0].message.content

    @api.model
    def convert_to_text(self, audio_path):
        """ Function for converting the audio from the file into text using AI.
            It returns the text.
        """
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'chatgpt_odoo_connector.api_key')
        client = OpenAI(api_key=api_key)
        try:
            audio_file = open(audio_path, "rb")
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            remove(audio_path)
        except Exception as e:
            return f'Error: {str(e)}'
        return transcription.text
