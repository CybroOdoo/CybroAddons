#*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
import base64
import json
import openai

from odoo import _
from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request


class TranscriptionController(http.Controller):
    """Transcription controllers for the Meeting Summarizer module."""

    # ------------------------------------------------------------------
    # Store incremental transcription chunks
    # ------------------------------------------------------------------
    @http.route('/get/transcription_data', methods=['POST'],
                type='jsonrpc', auth='public')
    def get_transcription_file(self, data, id, userId=None, timestamp=None,
                               **kwargs):
        """Store a transcription chunk in ir.config_parameter."""
        transcription_id = id
        if not transcription_id:
            return {'error': 'No ID provided'}

        cache_key = f"transcription_id_{transcription_id}"
        stored_data = request.env['ir.config_parameter'].sudo().get_param(
            cache_key)
        transcription_list = json.loads(stored_data) if stored_data else []
        transcription_list.append({
            'data': data,
            'userId': userId,
            'timestamp': timestamp,
        })
        request.env['ir.config_parameter'].sudo().set_param(
            cache_key, json.dumps(transcription_list))
        return {'message': 'Data stored successfully', 'cache_key': cache_key}

    # ------------------------------------------------------------------
    # Build transcription + summary files (called when call starts)
    # ------------------------------------------------------------------
    @http.route('/create/transcription_file_summary', methods=['POST'],
                type='jsonrpc', auth='user')
    def get_cached_transcription_file(self, id, **kwargs):
        """Read cached transcription data, call OpenAI, create ir.attachment records."""
        transcription_id = id
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
                model="gpt-4o-mini",
                messages=[
                    {"role": "system",
                     "content": "Summarize the following meeting transcript."},
                    {"role": "user", "content": content},
                ],
                temperature=0.7,
                max_tokens=500,
            )
            return response

        try:
            summary_data = create_summary(text_content)
            summary_text = summary_data.choices[0].message.content
        except Exception as e:
            summary_text = _("AI Summary could not be generated due to an API error.\nError Details: %s") % str(e)

        file_data = base64.b64encode(summary_text.encode("utf-8"))
        file_name = f"transcription_id_{transcription_id}.txt"
        summary_file_name = f"summary_id_{transcription_id}.txt"
        new_file_base64 = base64.b64encode(
            text_content.encode('utf-8')).decode('utf-8')

        def get_attachment(attachment_name):
            return request.env['ir.attachment'].sudo().search([
                ('name', '=', attachment_name),
                ('res_model', '=', 'ir.attachment'),
                ('res_id', '=', transcription_id),
            ], limit=1)

        attachment = get_attachment(file_name)
        summary_attachment = get_attachment(summary_file_name)

        if attachment or summary_attachment:
            existing_summary_content = base64.b64decode(
                summary_attachment.datas).decode('utf-8')
            updated_summary_content = existing_summary_content + "\n" + text_content
            attachment.sudo().write({
                'datas': base64.b64encode(
                    text_content.encode('utf-8')).decode('utf-8')
            })
            try:
                summary_data_update = create_summary(updated_summary_content)
                summary_text = summary_data_update.choices[0].message.content
            except Exception as e:
                summary_text = existing_summary_content + "\n" + _("(AI Summary Update failed: %s)") % str(e)
            summary_attachment.sudo().write({
                'datas': base64.b64encode(
                    summary_text.encode('utf-8')).decode('utf-8')
            })
        else:
            def create_attachment(filename, datas):
                return request.env['ir.attachment'].sudo().create({
                    'name': filename,
                    'datas': datas,
                    'res_model': 'ir.attachment',
                    'res_id': transcription_id,
                    'type': 'binary',
                    'mimetype': 'text/plain',
                })
            attachment = create_attachment(file_name, new_file_base64)
            summary_attachment = create_attachment(summary_file_name, file_data)

        return {
            'success': True,
            'transcriptionId': attachment.id,
            'summaryId': summary_attachment.id,
        }

    # ------------------------------------------------------------------
    # Retrieve IDs of the transcription + summary attachments
    # ------------------------------------------------------------------
    @http.route('/get/transcription_data/summary', methods=['POST'],
                type='jsonrpc', auth='public')
    def get_transcription_data_summary(self, channelId=False, **kwargs):
        """Return the transcription and summary attachment IDs for a channel."""
        transcription_id = False
        summary_id = False
        if not channelId:
            return {'transcriptionId': False, 'summaryId': False}

        attachments = request.env['ir.attachment'].sudo().search([
            ('name', 'in', [f"transcription_id_{channelId}.txt", f"summary_id_{channelId}.txt"]),
        ], order='id desc')
        for attachment in attachments:
            if attachment.name == f"transcription_id_{channelId}.txt" and not transcription_id:
                transcription_id = attachment.id
            elif attachment.name == f"summary_id_{channelId}.txt" and not summary_id:
                summary_id = attachment.id

        return {
            'transcriptionId': transcription_id,
            'summaryId': summary_id,
        }

    # ------------------------------------------------------------------
    # Create a send.mail.transcription record
    # ------------------------------------------------------------------
    @http.route('/create/send_transcription/record', methods=['POST'],
                type='jsonrpc', auth='public')
    def get_send_transcription_id(self, partnerIds=None, subject='',
                                  email_body='', transcriptionId=None,
                                  summaryId=None, **kwargs):
        """Create a send.mail.transcription wizard record and return its id."""
        transcription_attachment = request.env['ir.attachment'].sudo().browse(
            transcriptionId) if transcriptionId else request.env['ir.attachment']
        summary_attachment = request.env['ir.attachment'].sudo().browse(
            summaryId) if summaryId else request.env['ir.attachment']

        record = request.env['send.mail.transcription'].create({
            'partner_ids': partnerIds or [],
            'subject': subject,
            'email_body': email_body,
            'transcription_attachment_ids': transcription_attachment,
            'summary_attachment_ids': summary_attachment,
        })

        if transcription_attachment:
            transcription_attachment.sudo().write({
                'res_model': 'send.mail.transcription',
                'res_id': record.id,
            })
        if summary_attachment:
            summary_attachment.sudo().write({
                'res_model': 'send.mail.transcription',
                'res_id': record.id,
            })

        return record.id

    # ------------------------------------------------------------------
    # Check auto-mail settings and return participant details
    # ------------------------------------------------------------------
    @http.route('/check/auto_mail_send', methods=['POST'],
                type='jsonrpc', auth='public')
    def check_auto_mail_send(self, channelId=False, **kwargs):
        """Return participant details based on auto-mail configuration."""
        auto_mail_send = request.env['ir.config_parameter'].sudo().get_param(
            "meeting_summarizer.auto_mail_send")

        select_users = request.env['ir.config_parameter'].sudo().get_param(
            "meeting_summarizer.select_user")

        participants = []
        if auto_mail_send and select_users and channelId:
            partner_details = request.env['discuss.channel.member'].sudo().search(
                [('channel_id', '=', int(channelId))])
            host = request.env['discuss.channel'].browse(int(channelId))
            for rec in partner_details:
                rec_user = request.env['res.users'].search(
                    [('partner_id', '=', rec.partner_id.id)])
                if rec_user:
                    if select_users == 'host':
                        participants.append({
                            'partner_id': host.create_uid.partner_id.id,
                            'email': host.create_uid.email,
                        })
                        break
                    if rec_user.has_group('base.group_user'):
                        participants.append({
                            'partner_id': rec.partner_id.id,
                            'email': rec.partner_id.email,
                        })
        return participants

    # ------------------------------------------------------------------
    # Send automatic email with attachments
    # ------------------------------------------------------------------
    @http.route('/send/auto_email', methods=['POST'],
                type='jsonrpc', auth='public')
    def send_auto_mail(self, partners_email=None, subject='', email_body='',
                       transcriptionId=None, summaryId=None, **kwargs):
        """Send meeting transcription email automatically."""
        if not partners_email:
            return {'error': 'No valid email addresses found.'}

        from_mail = request.env.user.email
        attachment_ids = []
        if transcriptionId:
            attachment_ids.append((4, transcriptionId))
        if summaryId:
            attachment_ids.append((4, summaryId))

        email_values = {
            'email_from': from_mail,
            'email_to': ','.join(partners_email),
            'subject': subject,
            'body_html': email_body,
            'attachment_ids': attachment_ids,
        }
        email = request.env['mail.mail'].sudo().create(email_values)
        email.send()
        return True

    # ------------------------------------------------------------------
    # Return the channel creator user id
    # ------------------------------------------------------------------
    @http.route('/get/Meeting/creator', methods=['POST'],
                type='jsonrpc', auth='public')
    def get_meeting_creator(self, channelId=False, **kwargs):
        """Return the uid of the channel creator."""
        if not channelId:
            return False
        channel = request.env['discuss.channel'].sudo().browse(int(channelId))
        return channel.create_uid.id

    # ------------------------------------------------------------------
    # Post transcription+summary as a channel message
    # ------------------------------------------------------------------
    @http.route('/attach/transcription_data/summary', methods=['POST'],
                type='jsonrpc', auth='public')
    def attach_transcription_data_summary(self, channelId=False, transcriptionId=False, summaryId=False, **kwargs):
        """Attach the transcription and summary files as a channel message."""
        if not channelId:
            return False

        if not transcriptionId or not summaryId:
            attachments = request.env['ir.attachment'].sudo().search([
                ('name', 'in', [f"transcription_id_{channelId}.txt", f"summary_id_{channelId}.txt"]),
            ], order='id desc')
            for attachment in attachments:
                if attachment.name == f"transcription_id_{channelId}.txt" and not transcriptionId:
                    transcriptionId = attachment.id
                elif attachment.name == f"summary_id_{channelId}.txt" and not summaryId:
                    summaryId = attachment.id

        channel = request.env['discuss.channel'].sudo().browse(int(channelId))
        attachment_ids = list(filter(None, [transcriptionId, summaryId]))
        odoo_bot_user = request.env.ref('base.user_root')
        channel.with_user(odoo_bot_user).message_post(
            body="📝 Meeting transcription and summary are now available.",
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
            attachment_ids=attachment_ids,
        )
        return True
