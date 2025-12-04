# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
"""
This module defines HTTP controllers for handling transcription-related requests
in the Meeting Summarizer module, including interactions with the OpenAI API.
"""
import base64
import json
import openai

from odoo import _
from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request


class TranscriptionController(http.Controller):
    """Transcription controllers"""
    @http.route('/get/transcription_data', type='json', auth='public')
    def get_transcription_file(self, **kwargs):
        """Controller is used to store the transcription data"""
        transcription_id = kwargs['id']
        if not transcription_id:
            return {'error': 'No ID provided'}
        cache_key = f"transcription_id_{transcription_id}"
        stored_data = request.env['ir.config_parameter'].sudo().get_param(
            cache_key)
        if stored_data:
            transcription_list = json.loads(stored_data)
        else:
            transcription_list = []
        transcription_list.append(kwargs)
        request.env['ir.config_parameter'].sudo().set_param(cache_key,
                                                            json.dumps(
                                                                transcription_list))
        return {'message': 'Data stored successfully', 'cache_key': cache_key}

    @http.route('/create/transcription_file_summary', type='json', auth='user')
    def get_cached_transcription_file(self, **kwargs):
        """Get the data from ir_config parameter and create
        transcription file and summary file in ir_attachment"""
        transcription_id = kwargs.get('kwargs', {}).get('id')
        if not transcription_id:
            return {'error': 'No ID provided'}
        cache_key = f"transcription_id_{transcription_id}"
        cached_data = request.env['ir.config_parameter'].sudo().get_param(
            cache_key)
        if not cached_data:
            return {'error': 'No cached data found'}
        cached_data = json.loads(cached_data)
        text_content = "\n".join(item["data"] for item in cached_data)
        api_key = request.env['ir.config_parameter'].sudo().get_param(
            "meeting_summarizer.open_api_key")
        if not api_key:
            raise ValidationError(
                _("Please Enter a valid api key in settings.."))
        client = openai.OpenAI(api_key=api_key)
        def create_summary(content):
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system",
                     "content": "Summarize the following meeting transcript."},
                    {"role": "user", "content": content}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response
        summary_data = create_summary(text_content)
        summary_text = summary_data.choices[0].message.content  # Corrected response extraction
        file_data = base64.b64encode(summary_text.encode("utf-8"))
        file_name = f"transcription_id_{transcription_id}.txt"
        summary_file_name = f"summary_id_{transcription_id}.txt"
        new_file_content = text_content.encode('utf-8')
        new_file_base64 = base64.b64encode(new_file_content).decode('utf-8')
        def get_attachment(attachment_name):
            attachment_detail = request.env['ir.attachment'].sudo().search([
                ('name', '=', attachment_name),
                ('res_model', '=', 'ir.attachment'),
                ('res_id', '=', transcription_id)
            ], limit=1)
            return attachment_detail
        attachment = get_attachment(file_name)
        summary_attachment = get_attachment(summary_file_name)

        if attachment or summary_attachment:
            existing_summary_content = (
                base64.b64decode(summary_attachment.datas).decode('utf-8'))
            updated_summary_content = (
                    existing_summary_content + "\n" + text_content)  # Append new data

            attachment.sudo().write({
                'datas': base64.b64encode(
                    text_content.encode('utf-8')).decode('utf-8')
            })
            summary_data_update = (
                create_summary(updated_summary_content))
            summary_text = (
                summary_data_update.choices[0].message.content)  # Corrected response extraction
            summary_attachment.sudo().write({
                'datas': base64.b64encode(summary_text.encode('utf-8')).decode(
                    'utf-8')
            })
        else:
            def create_attachment(filename, datas):
                file = request.env['ir.attachment'].sudo().create({
                    'name': filename,
                    'datas': datas,
                    'res_model': 'ir.attachment',
                    'res_id': transcription_id,
                    'type': 'binary',
                    'mimetype': 'text/plain',
                })
                return file
            attachment = create_attachment(file_name, new_file_base64)
            summary_attachment = create_attachment(summary_file_name, file_data)
        return {'success': True, 'attachment_id': attachment.id, 'summary': summary_attachment.id}

    @http.route('/get/transcription_data/summary', type='json', auth='public')
    def get_transcription_data_summary(self, **kwargs):
        """Controller for return the specific transcription and summary file"""
        transcription_id = False
        summary_id = False
        channel_id = kwargs['kwargs'].get('channelId', False)
        attachments = request.env['ir.attachment'].sudo().search(
            [('res_id', '=', int(channel_id)),
             ('res_model', '=', 'ir.attachment')])

        for attachment in attachments:
            if attachment.name == f"transcription_id_{channel_id}.txt":
                transcription_id = attachment.id
            else:
                summary_id = attachment.id
        return {'transcriptionId': transcription_id,
                'summaryId': summary_id}

    @http.route('/create/send_transcription/record', type='json', auth='public')
    def get_send_transcription_id(self, **kwargs):
        """create a record in send_mail_transcription using partner_ids,subject
         email_body,transcription_attachment_ids, summary_attachment_ids and
         return the corresponding record id"""
        subject = kwargs['kwargs'].get('subject')
        email_body = kwargs['kwargs'].get('email_body')
        partner_ids = kwargs['kwargs'].get('partnerIds')
        transcription_id = kwargs['kwargs'].get('transcriptionId')
        summary_id = kwargs['kwargs'].get('summaryId')
        transcription_id = request.env['ir.attachment'].browse(transcription_id)
        summary_id = request.env['ir.attachment'].browse(summary_id)
        send_mail_transcription_id = request.env['send.mail.transcription'].create(
            {'partner_ids': partner_ids,
             'subject': subject,
             'email_body': email_body,
             'transcription_attachment_ids': transcription_id,
             'summary_attachment_ids': summary_id})
        return send_mail_transcription_id.id

    @http.route('/check/auto_mail_send', type='json', auth='public')
    def check_auto_mail_send(self, **kwargs):
        """Here checking the configuration settings that auto_mail_send_option
         enable or not and also get all the values from that and return the
         specific participant details"""
        channel_id = kwargs['kwargs'].get('channelId', False)
        auto_mail_send = request.env['ir.config_parameter'].sudo().get_param(
            "meeting_summarizer.auto_mail_send")

        select_users = request.env['ir.config_parameter'].sudo().get_param(
            "meeting_summarizer.select_user")

        participants = []
        if auto_mail_send and select_users:
            partner_details = request.env['discuss.channel.member'].sudo().search(
                [('channel_id', '=', channel_id)]
            )
            host = request.env['discuss.channel'].browse(channel_id)
            for rec in partner_details:
                user = request.env['res.users'].search(
                    [('partner_id', '=', rec.partner_id.id)]
                )
                if user:
                    if select_users == 'host':
                        participants.append({
                            'partner_id': host.create_uid.partner_id.id,
                            'email': host.create_uid.email
                        })
                        break  # Exit the loop after adding the host, no need for further logic
                    if user.has_group('base.group_user'):
                        participants.append({
                            'partner_id': rec.partner_id.id,
                            'email': rec.partner_id.email
                        })
        return participants

    @http.route('/send/auto_email', type='json', auth='public')
    def send_auto_mail(self, **kwargs):
        """Here sending automatic mail for selected users in settings."""
        transcription_id = kwargs['kwargs'].get('transcriptionId')
        summary_id = kwargs['kwargs'].get('summaryId')
        email_body = kwargs['kwargs'].get('email_body')
        subject = kwargs['kwargs'].get('subject')
        partners_email = kwargs['kwargs'].get('partners_email',
                                            [])
        if not partners_email:
            return {
                'error': 'No valid email addresses found for the selected partners.'}
        from_mail = request.env.user.email
        attachment_ids = []
        if transcription_id and summary_id:
            attachment_ids.append((4, transcription_id))
            attachment_ids.append((4, summary_id))
        email_values = {
            'email_from': from_mail,
            'email_to': ','.join(partners_email),  # Convert email list to string
            'subject': subject,
            'body_html': email_body,
            'attachment_ids': attachment_ids,  # Attach files if available
        }
        email = request.env['mail.mail'].sudo().create(email_values)
        email.send()
        return True

    @http.route('/get/Meeting/creator', type='json', auth='public')
    def get_meeting_creator(self, **kwargs):
        """Return the channel creator"""
        channel_id = kwargs['kwargs'].get('channelId', False)
        channel_details = request.env['discuss.channel'].sudo().browse(channel_id)
        return channel_details.create_uid.id

    @http.route('/attach/transcription_data/summary', type='json',
                auth='public')
    def attach_transcription_data_summary(self, **kwargs):
        """Controller for return the specific transcription and summary file"""
        transcription_id = False
        summary_id = False
        channel_id = kwargs['kwargs'].get('channelId', False)
        attachments = request.env['ir.attachment'].sudo().search(
            [('res_id', '=', int(channel_id)),
             ('res_model', '=', 'ir.attachment')])
        for attachment in attachments:
            if attachment.name == f"transcription_id_{channel_id}.txt":
                transcription_id = attachment.id
            else:
                summary_id = attachment.id

        channel = request.env['discuss.channel'].sudo().browse(int(channel_id))
        attachment_ids = list(filter(None, [transcription_id, summary_id]))
        odoo_bot_user = request.env.ref('base.user_root')
        channel.with_user(odoo_bot_user).message_post(
            body="📝 Meeting transcription and summary are now available.",
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
            attachment_ids=attachment_ids
        )
        return True
