# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
################################################################################
import re
import time
import threading
import base64
import requests
from datetime import datetime, timezone, UTC
from markupsafe import Markup
from odoo import api, fields, models
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


def remove_html(string):
    regex = re.compile(r'<[^>]+>')
    return regex.sub('', string)


class MailMessage(models.Model):
    """Inherited to add more field and functions"""
    _inherit = 'mail.message'

    is_slack = fields.Boolean(string="Slack",
                              help="True for Slack connected messages")
    channel = fields.Many2one('discuss.channel', string="Channel",
                              help="Channel corresponds to the message")
    slack_message_ts = fields.Char()
    is_slack_pending = fields.Boolean(string="Pending")
    slack_msg_id = fields.Char()

    @api.model
    def create(self, vals):
        """Over-riding the create method to send message to slack"""
        res = super().create(vals)
        if not self.env.company.slack_sync:
            return res
        discuss_channel = self.env['discuss.channel']
        channels = discuss_channel.search([('is_slack', '=', True)])
        if not channels:
            return res
        admin_slack_user = self.env['slack.user'].search([
            ('res_company_id', '=', self.env.company.id),
            ('user', '=', self.env.user.slack_user_ref)
        ], limit=1)
        is_bot = False
        if admin_slack_user and admin_slack_user.user_token:
            # Admin is sending — use their personal xoxp- token-----------
            token = admin_slack_user.user_token
        else:
            # Regular user — use bot token with username override
            token = self.env.user.company_id.bot_token
            is_bot = True
        if not token:
            raise UserError('No Token found in Odoo for either BOT or Slack Admin User')
        if not token:
            return res
        # ── Collect all data BEFORE starting thread ────────────────────────────
        messages_data = []
        for channel in channels:
            msgs = self.search([
                ('model', '=', 'discuss.channel'),
                ('res_id', '=', channel.id),
                ('is_slack', '=', False),
                ('slack_message_ts', '=', False),
            ])
            if self.env.context.get('is_slack'):
                msgs -= res
                # only do the slack pending workflow messages with attachments where only for them, we are using a
                # different posting methods which at first we won't get the message ts for matching Odoo and Slack
                # messages to sync
                if res.attachment_ids:
                    res.write({
                        'is_slack_pending': True
                    })
            if not msgs:
                continue
            for rec in msgs:
                # Collect attachments as raw bytes before thread starts
                attachments_data = []
                for att in rec.attachment_ids:
                    try:
                        attachments_data.append({
                            'name': att.name,
                            'content': base64.b64decode(att.datas),
                            'mimetype': att.mimetype or 'application/octet-stream',
                        })
                    except Exception as e:
                        _logger.info(f'Error reading attachment {att.name}: {e}')
                messages_data.append({
                    'rec_id': rec.id,
                    'text': f"{remove_html(rec.body or '')}",
                    'author': rec.author_id.name if rec.author_id else self.env.user.name,
                    'channel_name': rec.record_name,
                    'channel_id': channel.id,
                    'attachments': attachments_data,  # raw bytes, no DB needed
                })
        if not messages_data:
            return res
        # ── Start thread with all data already collected ───────────────────────
        threading.Thread(
            target=self._sync_messages_to_slack,
            args=(messages_data, token, self.env.user.name, is_bot),
            daemon=True
        ).start()
        return res

    def _sync_messages_to_slack(self, messages_data, token, user, is_bot):
        """Sync messages to Slack in background — all data passed in, no DB reads"""
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json; charset=utf-8',
        }
        # Fetch Slack channel map once
        slack_channel_map = self._get_slack_channel_map(headers)
        for msg in messages_data:
            try:
                slack_ts, uploaded_file_ids = self._send_single_message_to_slack(
                    msg=msg,
                    headers=headers,
                    slack_channel_map=slack_channel_map,
                    user=user, is_bot=is_bot
                )
                # ── Write result back to DB ────────────────────────────────────
                if slack_ts and slack_ts is not None:
                    try:
                        with self.pool.cursor() as cr:
                            env = api.Environment(cr, self.env.uid, self.env.context)
                            rec = env['mail.message'].sudo().browse(msg['rec_id'])
                            rec.write({
                                'is_slack': True,
                                'slack_message_ts': slack_ts,
                            })
                            cr.commit()
                    except Exception as e:
                        _logger.info(f'DB write error for message {msg["rec_id"]}: {e}')
                elif uploaded_file_ids:
                    time.sleep(3)
                    with self.pool.cursor() as cr:
                        env = api.Environment(cr, self.env.uid, self.env.context)
                        channel = env['discuss.channel'].sudo().browse(msg['channel_id'])
                        mail_message = env['mail.message'].sudo().browse(msg['rec_id'])
                        history_response = requests.get(
                            'https://slack.com/api/conversations.history',
                            headers=headers,
                            params={
                                'channel': channel.channel,
                                'limit': 10,
                            },
                            timeout=10,
                        )
                        history_data = history_response.json()
                        for message in history_data.get('messages', []):
                            file_ids = [
                                f.get('id')
                                for f in message.get('files', [])
                            ]
                            if any(fid in file_ids for fid in uploaded_file_ids):
                                mail_message.write({'slack_message_ts': message.get('ts'),
                                                    'is_slack_pending': False,
                                                    })
            except Exception as e:
                _logger.info(f'Error syncing message {msg["rec_id"]} to Slack: {e}')
        # Update channel msg_date
        try:
            with self.pool.cursor() as cr:
                env = api.Environment(cr, self.env.uid, self.env.context)
                for msg in messages_data:
                    env['discuss.channel'].sudo().browse(msg['channel_id']).write({
                        'msg_date': fields.Datetime.now(),
                    })
                cr.commit()
        except Exception as e:
            _logger.info(f'Error updating channel msg_date: {e}')

    def _send_single_message_to_slack(self, msg, headers, slack_channel_map, user, is_bot):
        """Send one message to Slack, returns slack ts or None on failure"""
        if is_bot:
            text = f"{user}: {msg.get('text')}" if msg.get('text') else None
        else:
            text = msg.get('text') if msg.get('text') else None
        channel_name = msg['channel_name'].lstrip('#')
        attachments = msg['attachments']
        slack_channel_id = (
                slack_channel_map.get(channel_name) or
                slack_channel_map.get(f'#{channel_name}')
        )
        if not slack_channel_id:
            return None
        if attachments:
            # ── Upload files first ─────────────────────────────────────────────
            uploaded_file_ids = self._upload_attachments_to_slack(
                attachments=attachments,
                headers=headers
            )
            if uploaded_file_ids:
                pass
                complete_response = requests.post(
                    'https://slack.com/api/files.completeUploadExternal',
                    headers=headers,
                    json={
                        'files': [{'id': fid} for fid in uploaded_file_ids],
                        'channel_id': slack_channel_id,
                        'initial_comment': text or '',
                    },
                    timeout=15,
                )
                complete_data = complete_response.json()
                with self.pool.cursor() as cr:
                    env = api.Environment(cr, self.env.uid, self.env.context)
                    mail_message = env['mail.message'].sudo().browse(msg['rec_id'])
                    mail_message.write({
                        'is_slack_pending': True,
                        'slack_msg_id': ','.join(uploaded_file_ids),
                    })
                if complete_data.get('ok'):
                    return (
                        complete_data.get('files', [{}])[0]
                        .get('shares', {})
                        .get('public', {})
                        .get(slack_channel_id, [{}])[0]
                        .get('ts', '')
                    ), uploaded_file_ids
                else:
                    return None, None
            elif text:
                # Attachments failed — fallback to text only
                return self._post_text_message_to_slack(
                    text, msg['channel_name'], headers
                ), None
            else:
                return None, None
        else:
            # ── Text only ──────────────────────────────────────────────────────
            return self._post_text_message_to_slack(
                text, msg['channel_name'], headers
            ), None

    def _post_text_message_to_slack(self, text, channel_name, headers):
        """Send plain text message, returns ts or None"""
        try:
            payload = {
                    'channel': channel_name,
                    'text': text or '',
                }
            response = requests.post(
                'https://slack.com/api/chat.postMessage',
                headers=headers,
                json=payload,
                timeout=10,
            )
            req_response = response.json()
            if req_response.get('ok'):
                return req_response.get('message', {}).get('ts', '')
            else:
                return None
        except Exception as e:
            _logger.info(f'Error posting text to Slack: {e}')
            return None

    def _upload_attachments_to_slack(self, attachments, headers):
        """Upload attachments from raw bytes data, return list of file IDs"""
        file_ids = []
        for attachment in attachments:
            try:
                file_content = attachment['content']  # raw bytes, no DB needed
                file_name = attachment['name']
                mime_type = attachment['mimetype']
                # Step 1: Get upload URL
                url_response = requests.post(
                    'https://slack.com/api/files.getUploadURLExternal',
                    headers=headers,
                    params={
                        'filename': file_name,
                        'length': len(file_content),
                    },
                    timeout=10,
                )
                url_data = url_response.json()
                if not url_data.get('ok'):
                    _logger.info(f'Failed to get upload URL for {file_name}: %s', url_data.get('error'))
                    continue
                upload_url = url_data['upload_url']
                file_id = url_data['file_id']
                # Step 2: Upload raw bytes
                upload_response = requests.post(
                    upload_url,
                    data=file_content,
                    headers={'Content-Type': mime_type},
                    timeout=30,
                )
                if upload_response.status_code in (200, 201):
                    file_ids.append(file_id)
                else:
                    _logger.info(f'File upload failed for {file_name}')
            except Exception as e:
                _logger.info(f'Error uploading file to Slack: {e}')
        return file_ids

    def _get_slack_channel_map(self, headers):
        """Fetch all Slack channels once, return name→id map"""
        channel_map = {}
        try:
            response = requests.post(
                'https://slack.com/api/conversations.list',
                headers=headers,
                params={'limit': 200},
                timeout=10,
            )
            data = response.json()
            if data.get('ok'):
                for c in data.get('channels', []):
                    channel_map[c['name']] = c['id']
                    channel_map[f"#{c['name']}"] = c['id']
        except Exception as e:
            _logger.info(f'Error getting channel map: {e}')
        return channel_map

    def _format_slack_text(self, text):
        if not text:
            return ''
        # <url|text>
        text = re.sub(
            r'<(.*?)\|(.*?)>',
            r'<a href="\1" target="_blank" rel="noopener noreferrer">\2</a>',
            text
        )
        # <url>
        text = re.sub(
            r'<(https?://.*?)>',
            r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>',
            text
        )
        text = text.replace('\n', '<br/>')
        return text

    def _parse_blocks(self, blocks):
        """Parse the block for getting the correct messages even if they are links attached"""
        html = ''
        for block in blocks:
            if block.get('type') == 'rich_text':
                for el in block.get('elements', []):
                    for item in el.get('elements', []):
                        if item['type'] == 'text':
                            html += item.get('text', '')
                        elif item['type'] == 'link':
                            url = item.get('url')
                            text = item.get('text', url)
                            html += f'<a href="{url}">{text}</a>'
                        elif item['type'] == 'emoji':
                            html += f":{item.get('name')}:"
                html += '<br/>'
        return html

    def _get_attachments(self, files, channel_id):
        """Get the full attachments of any type and create in odoo with the specific content type"""
        attachments = self.env['ir.attachment']
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {self.env.user.company_id.bot_token}",
            "User-Agent": "Mozilla/5.0",  # ✅ important for Slack
        })
        for f in files:
            url = f.get("url_private_download")
            headers = {
                'Authorization': f'Bearer {self.env.user.company_id.bot_token}'
            }
            try:
                res = requests.get(url, headers=headers, stream=True)
                if res.status_code == 200:
                    content_type = res.headers.get('Content-Type', '')
                    # ❌ Skip HTML (invalid auth)
                    if 'text/html' in content_type:
                        continue
                    file_data = res.content
                    res = session.get(url, allow_redirects=True)
                    attachment_vals = {
                        'name': f.get('name'),
                        'datas': base64.b64encode(file_data),
                        'res_model': 'discuss.channel',
                        'res_id': channel_id.id,
                        'mimetype': content_type,
                    }
                    attachments |= self.env['ir.attachment'].create(attachment_vals)
            except Exception as e:
                _logger.info(f'Error getting attachments: {e}')
        return attachments

    def action_synchronization_slack(self):
        """scheduled action to retrieve message from Slack"""
        if self.env.company.slack_sync:
            discuss_channel = self.env['discuss.channel']
            res_user = self.env['res.users']
            channels = discuss_channel.search([('is_slack', '=', 'true')])
            headers = {'Authorization': 'Bearer ' + self.env.user.company_id.bot_token}
            for channel_id in channels:
                url = "https://slack.com/api/conversations.history?channel=%s" % channel_id.channel
                params = {}
                if channel_id.msg_date:
                    dt = channel_id.msg_date.replace(tzinfo=timezone.utc)
                    oldest = dt.timestamp()
                    params.update({
                        "oldest": str(oldest),
                    })
                response = requests.get(url, headers=headers, params=params)
                channels_history = response.json()
                if not channels_history.get('ok'):
                    continue
                messages = channels_history.get('messages', [])
                messages.reverse()
                # Initialize msg_date if not set
                if not channel_id.msg_date:
                    now = fields.Datetime.now()
                    channel_id.msg_date = now
                    continue
                for item in messages:
                    user_id = item.get('user')
                    if not user_id:
                        continue
                    # search for existing message
                    msg = self.env['mail.message'].search([('slack_message_ts', '=', item['ts'])])
                    if msg:
                        continue
                    user = res_user.search([('slack_user_ref', '=', user_id)], limit=1)
                    if not user:
                        url_users = "https://slack.com/api/users.list"
                        # --- Fetch users ---
                        response = requests.get(url_users, headers=headers)
                        data = response.json()
                        if not data.get("ok"):
                            raise UserError(f"Slack API Error: {data.get('error')}")
                        members = data.get("members", [])
                        # --- Sync users ---
                        self.env.user.action_sync_users(members)
                    if item.get('subtype') in ['channel_join']:
                        continue
                    # BODY
                    if item.get('blocks'):
                        body = self._parse_blocks(item['blocks'])
                    else:
                        body = self._format_slack_text(item.get('text'))
                    # ATTACHMENTS
                    attachments = []
                    if item.get('files'):
                        attachments = self._get_attachments(item['files'], channel_id)
                    # Slack timestamp → UTC datetime
                    converted_time = datetime.fromtimestamp(float(item['ts']), UTC)
                    # Ensure msg_date is datetime (Odoo usually already is)
                    msg_date_dt = channel_id.msg_date
                    if isinstance(msg_date_dt, str):
                        msg_date_dt = fields.Datetime.from_string(msg_date_dt)
                    if msg_date_dt:
                        msg_date_dt = msg_date_dt.replace(tzinfo=UTC)
                    # Compare in UTC (no timezone conversion needed)
                    if msg_date_dt and converted_time > msg_date_dt:
                        msg = channel_id.with_user(user.id).with_context(is_slack=True).message_post(
                            body=Markup(body),
                            message_type='comment',
                            subtype_xmlid='mail.mt_comment',
                            attachment_ids=attachments.ids if attachments else attachments
                        )
                        msg.is_slack = True
                        msg.slack_message_ts = item['ts']
                # Update msg_date once after processing
                # Current UTC time (Odoo standard)
                now = fields.Datetime.now()
                channel_id.msg_date = now
