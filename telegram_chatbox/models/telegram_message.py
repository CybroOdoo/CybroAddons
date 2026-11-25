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
                    f"https://api.telegram.org/bot{bot.sudo().token}/answerCallbackQuery",
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
            if partner.telegram_chat_id != chat_id or partner.telegram_username != username:
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
        attachment = self._handle_telegram_attachments(bot, msg_record, message)
        attachment_ids = [attachment.id] if attachment else (msg_record.attachment_ids.ids if msg_record.attachment_ids else [])

        media_desc = ""
        if attachment:
            media_desc = f"📎 {attachment.name}"
        elif msg_record.attachment_ids:
            media_desc = f"📎 {', '.join(msg_record.attachment_ids.mapped('name'))}"

        if text and media_desc:
            body_content = Markup("%s<br/>%s") % (escape(text).replace('\n', Markup('<br/>')), escape(media_desc))
        elif text:
            body_content = escape(text).replace('\n', Markup('<br/>'))
        elif media_desc:
            body_content = escape(media_desc)
        elif message.get("sticker"):
            emoji = message["sticker"].get("emoji", "")
            body_content = f"Sticker {emoji}".strip()
        else:
            body_content = "(empty message)"

        chatter_body = Markup("<b>Incoming Telegram:</b><br/>%s") % body_content

        author_id = msg_record.partner_id.id if msg_record.partner_id else False
        system_user = self.env.ref('base.user_root', raise_if_not_found=False) or self.env.ref('base.user_admin', raise_if_not_found=False)

        if doc_model and doc_id:
            record = self.env[doc_model].sudo().browse(doc_id)
            if record.exists():
                post_kwargs = {
                    'body': chatter_body,
                    'attachment_ids': attachment_ids,
                    'message_type': 'comment',
                }
                if author_id:
                    post_kwargs['author_id'] = author_id
                target = record.with_user(system_user) if system_user else record
                target.message_post(**post_kwargs)
        elif msg_record.partner_id:
            post_kwargs = {
                'body': chatter_body,
                'attachment_ids': attachment_ids,
                'message_type': 'comment',
            }
            if author_id:
                post_kwargs['author_id'] = author_id
            target = msg_record.partner_id.with_user(system_user) if system_user else msg_record.partner_id
            target.message_post(**post_kwargs)

        return msg_record



    def send_via_bot(self, text, bot=None, reply_markup=None):
        """Send an outgoing message via Telegram HTTP API."""

        for rec in self:
            bot = (bot or rec.bot_id).sudo()
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
                        rec.sudo().name = f"tg_{res_data['result'].get('message_id')}"

                for attachment in rec.attachment_ids:
                    file_data = False
                    if getattr(attachment, 'raw', None):
                        file_data = bytes(attachment.raw)
                    elif getattr(attachment, 'datas', None):
                        file_data = base64.b64decode(attachment.datas)

                    if file_data:
                        doc_url = f"https://api.telegram.org/bot{bot.token}/sendDocument"
                        files = {'document': (attachment.name or 'document', file_data, attachment.mimetype or 'application/octet-stream')}
                        doc_data = {'chat_id': rec.chat_id}
                        upload_timeout = max(bot.timeout or 15, 60)
                        r_doc = requests.post(doc_url, data=doc_data, files=files, timeout=upload_timeout)
                        if not r_doc.ok:
                            _logger.error("Telegram sendDocument failed: %s - %s", r_doc.status_code, r_doc.text)
                        r_doc.raise_for_status()

                rec.state = 'sent'
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

        elif message_data.get("sticker"):
            sticker = message_data["sticker"]
            thumb = sticker.get("thumbnail") or sticker.get("thumb")
            # If the sticker is animated (.tgs Lottie) or video (.webm), download the
            # static thumbnail (.webp) so the browser can natively render it in chatter.
            if (sticker.get("is_animated") or sticker.get("is_video")) and thumb and thumb.get("file_id"):
                file_id = thumb["file_id"]
                file_unique_id = thumb.get("file_unique_id", sticker.get("file_unique_id", "thumb"))
            else:
                file_id = sticker["file_id"]
                file_unique_id = sticker.get("file_unique_id", "sticker")

            mimetype = "image/webp"
            filename = f"sticker_{file_unique_id}.webp"

        elif message_data.get("animation"):
            file_id = message_data["animation"]["file_id"]
            file_unique_id = message_data["animation"]["file_unique_id"]
            mimetype = message_data["animation"].get("mime_type", "video/mp4")
            filename = message_data["animation"].get("file_name", f"animation_{file_unique_id}.mp4")

        if not file_id:
            return False

        bot = bot.sudo()
        binary_data = None
        for attempt in range(3):
            try:
                file_info_url = f"https://api.telegram.org/bot{bot.token}/getFile"
                r = requests.get(
                    file_info_url,
                    params={"file_id": file_id},
                    timeout=30,
                )
                r.raise_for_status()
                file_info = r.json()

                if not file_info.get("ok"):
                    _logger.error("Telegram getFile failed: %s", file_info)
                    break

                file_path = file_info["result"]["file_path"]
                download_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"
                r2 = requests.get(download_url, timeout=45)
                r2.raise_for_status()
                binary_data = r2.content
                break
            except (requests.exceptions.Timeout, requests.RequestException) as e:
                _logger.warning("Attempt %d/3 downloading Telegram attachment %s: %s", attempt + 1, file_id, e)
                if attempt < 2:
                    import time
                    time.sleep(1.5)
                else:
                    _logger.error("All 3 attempts to download Telegram attachment %s failed", file_id)

        if not binary_data:
            msg_record.state = 'error'
            return False

        try:
            attachment = self.env["ir.attachment"].sudo().create({
                "name": filename,
                "raw": binary_data,
                "store_fname": filename,
                "mimetype": mimetype,
                "res_model": 'telegram.message',
                "res_id": msg_record.id,
                "type": 'binary',
            })
            msg_record.sudo().write({'attachment_ids': [(4, attachment.id)]})

            return attachment

        except Exception as e:
            _logger.exception("Failed to create Odoo attachment: %s", e)
            msg_record.state = 'error'
            return False
