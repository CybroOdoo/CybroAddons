# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import base64
import logging
import requests
from markupsafe import Markup, escape
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class TelegramMessage(models.Model):
    """Model to store incoming and outgoing Telegram messages."""
    _name = "telegram.message"
    _description = "Telegram Message"
    _order = "date desc"

    name = fields.Char(
        string="Message ID",
        help="Unique identifier of the Telegram message."
    )

    direction = fields.Selection(
        [('incoming', 'Incoming'), ('outgoing', 'Outgoing')],
        default='incoming',
        help="Indicates whether the message was received from Telegram or sent from Odoo."
    )

    chat_id = fields.Char(
        index=True,
        help="Telegram chat ID associated with this conversation."
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        help="Contact linked to this Telegram conversation."
    )

    bot_id = fields.Many2one(
        'telegram.bot',
        string='Bot',
        help="Telegram bot used to send or receive this message."
    )

    res_model = fields.Char(
        string='Related Document Model',
        index=True,
        help="Model of the related document."
    )

    res_id = fields.Integer(
        string='Related Document ID',
        index=True,
        help="ID of the related document."
    )

    telegram_template_id = fields.Many2one(
        'telegram.template',
        string='Telegram Template',
        help="Template used to generate the message content."
    )

    message_text = fields.Text(
        string='Message',
        help="Content of the Telegram message."
    )

    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Attachments',
        help="Files attached to the Telegram message."
    )

    date = fields.Datetime(
        default=fields.Datetime.now,
        help="Date and time when the message was sent or received."
    )

    state = fields.Selection(
        [('new', 'Draft'), ('received', 'Received'),
         ('sent', 'Sent'), ('error', 'Failed')],
        help="Current status of the Telegram message."
    )
    @api.model
    def create_incoming(self, bot, payload):
        """Create a telegram.message from webhook payload. payload is the raw dict."""

        callback_query = payload.get('callback_query')
        if callback_query:
            message = callback_query.get('message') or {}
            chat = message.get('chat', {})
            text = callback_query.get('data') or ''

            try:
                requests.post(
                    f"https://api.telegram.org/bot{bot.token}/answerCallbackQuery",
                    json={"callback_query_id": callback_query.get('id')},
                    timeout=5
                )
            except Exception as e:
                _logger.warning("Failed to answer callback query: %s", e)
        else:
            message = payload.get('message') or payload.get('edited_message') or {}
            chat = message.get('chat', {})
            text = message.get('text') or message.get('caption') or ''

        if not chat.get('id'):
            _logger.warning(
                "Skipping Telegram update with no processable chat. "
                "Update type keys: %s", list(payload.keys())
            )
            return False

        chat_id = str(chat.get('id'))
        username = chat.get('username') or False
        first_name = chat.get('first_name') or ''
        last_name = chat.get('last_name') or ''
        full_name = ' '.join(filter(None, [first_name, last_name])) or False

        partner = self.env['res.partner'].sudo().search(
            [('telegram_chat_id', '=', chat_id)], limit=1)
        if not partner and username:
            partner = self.env['res.partner'].sudo().search(
                [('telegram_username', '=', username)],
                limit=1)
        if not partner and full_name:
            partner = self.env['res.partner'].sudo().search([
                ('name', '=', full_name)
            ])
        if not partner or len(partner) > 1:
            partner_vals = {
                'name': full_name or 'Telegram User',
                'telegram_chat_id': chat_id,
                'telegram_username': username,
            }
            partner = self.env['res.partner'].sudo().create(partner_vals)
        else:
            partner_vals = {
                'telegram_chat_id': chat_id,
                'telegram_username': username,
            }
            partner.sudo().write(partner_vals)

        reply_to = message.get('reply_to_message')
        doc_model = False
        doc_id = False

        if reply_to:
            orig_msg_id = reply_to.get('message_id')
            orig_msg = self.sudo().search([('name', '=', f"tg_{orig_msg_id}")], limit=1)
            if orig_msg:
                doc_model = orig_msg.res_model
                doc_id = orig_msg.res_id

        vals = {
            'name': message.get('message_id') and "tg_%s" % message.get(
                'message_id') or False,
            'direction': 'incoming',
            'chat_id': chat_id,
            'partner_id': partner.id,
            'bot_id': bot.id,
            'res_model': doc_model,
            'res_id': doc_id,
            'message_text': text,
            'state': 'received',
        }
        msg_record = self.sudo().create(vals)
        self._handle_telegram_attachments(bot, msg_record, message)

        chatter_body = Markup("<b>Incoming Telegram:</b><br/>%s") % (
            escape(text).replace('\n', Markup('<br/>')) if text else '(media message)'
        )

        if doc_model and doc_id:
            record = self.env[doc_model].sudo().browse(doc_id)
            if record.exists():
                record.message_post(
                    body=chatter_body,
                    attachment_ids=msg_record.attachment_ids.ids
                )
        elif msg_record.partner_id:
            msg_record.partner_id.message_post(
                body=chatter_body,
                attachment_ids=msg_record.attachment_ids.ids
            )

        return msg_record



    def send_via_bot(self, text, bot=None, reply_markup=None):
        """Send an outgoing message via Telegram HTTP API."""

        for rec in self:
            bot = bot or rec.bot_id
            if not bot or not bot.token or not rec.chat_id:
                rec.state = 'error'
                continue
            error_occurred = False

            try:
                if text:
                    url = f"https://api.telegram.org/bot{bot.token}/sendMessage"
                    payload = {"chat_id": rec.chat_id, "text": text}
                    if reply_markup is not None:
                        payload['reply_markup'] = reply_markup
                    r = requests.post(url, json=payload, timeout=bot.timeout)
                    r.raise_for_status()
                    res_data = r.json()
                    if res_data.get('ok') and res_data.get('result'):
                        rec.name = f"tg_{res_data['result'].get('message_id')}"

                for attachment in rec.attachment_ids:
                    if attachment.datas:
                        doc_url = f"https://api.telegram.org/bot{bot.token}/sendDocument"
                        file_data = base64.b64decode(attachment.datas)
                        files = {'document': (attachment.name or 'document', file_data, attachment.mimetype)}
                        doc_data = {'chat_id': rec.chat_id}
                        r_doc = requests.post(doc_url, data=doc_data, files=files, timeout=bot.timeout)
                        r_doc.raise_for_status()
                
                self.write({
                    'state': 'sent'
                })
            except Exception as e:
                _logger.exception("Failed to send telegram message or attachment: %s", e)
                error_occurred = True

            if error_occurred:
                rec.state = 'error'

    def _handle_telegram_attachments(self, bot, msg_record, message_data):
        """
        Download attachments (photo, document, voice, audio, video)
        with timeout + error handling.
        """
        file_id = False
        mimetype = False
        filename = False

        if message_data.get("photo"):
            file_id = message_data["photo"][-1]["file_id"]
            file_unique_id = message_data["photo"][-1]["file_unique_id"]
            mimetype = "image/jpeg"
            filename = f"photo_{file_unique_id}.jpg"

        elif message_data.get("document"):
            file_id = message_data["document"]["file_id"]
            file_unique_id = message_data["document"]["file_unique_id"]
            mimetype = message_data["document"].get("mime_type",
                                                    "application/octet-stream")
            filename = message_data["document"].get("file_name",
                                                    f"doc_{file_unique_id}")

        elif message_data.get("voice"):
            file_id = message_data["voice"]["file_id"]
            file_unique_id = message_data["voice"]["file_unique_id"]
            mimetype = "audio/ogg"
            filename = f"voice_{file_unique_id}.ogg"

        elif message_data.get("audio"):
            file_id = message_data["audio"]["file_id"]
            file_unique_id = message_data["audio"]["file_unique_id"]
            mimetype = "audio/mpeg"
            filename = message_data["audio"].get("file_name",
                                                 f"audio_{file_unique_id}.mp3")

        elif message_data.get("video"):
            file_id = message_data["video"]["file_id"]
            file_unique_id = message_data["video"]["file_unique_id"]
            mimetype = "video/mp4"
            filename = f"video_{file_unique_id}.mp4"

        if not file_id:
            return False

        try:
            file_info_url = f"https://api.telegram.org/bot{bot.token}/getFile"

            r = requests.get(
                file_info_url,
                params={"file_id": file_id},
                timeout=12,
            )
            r.raise_for_status()
            file_info = r.json()

            if not file_info.get("ok"):
                _logger.error("Telegram getFile failed: %s", file_info)
                msg_record.state = 'error'
                return False
            file_path = file_info["result"]["file_path"]
            download_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"
            r2 = requests.get(download_url, timeout=20)
            r2.raise_for_status()
            binary_data = r2.content
        except requests.exceptions.Timeout:
            msg_record.state = 'error'
            _logger.error("Timeout while downloading Telegram attachment %s",
                          file_id)
            return False
        except requests.RequestException as e:
            msg_record.state = 'error'
            _logger.exception(
                "Error downloading Telegram attachment %s: %s",
                file_id, e
            )
            return False

        try:
            encoded = base64.b64encode(binary_data).decode('ascii')
            attachment = self.env["ir.attachment"].sudo().create({
                "name": filename,
                "datas": encoded,
                "store_fname": filename,
                "mimetype": mimetype,
                "res_model": 'telegram.message',
                "res_id": msg_record.id,
                "type": 'binary',
            })
            msg_record.attachment_ids = [(4, attachment.id)]

            return attachment

        except Exception as e:
            _logger.exception("Failed to create Odoo attachment: %s", e)
            msg_record.state = 'error'
            return False
