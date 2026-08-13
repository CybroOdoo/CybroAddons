# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
###############################################################################
import base64
import datetime
from html import unescape
from urllib.parse import urlencode, parse_qs, urlparse
import requests
import logging

from bs4 import BeautifulSoup
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ZohoMailAccount(models.Model):
    """Model for configuring and managing Zoho Mail OAuth accounts.

        Stores Zoho OAuth credentials, account information, tokens, folder IDs,
        connection state, and Zoho region details required to integrate a Zoho
        Mail account with Odoo.
        """
    _name = 'zoho.mail.account'
    _description = 'Zoho Mail Account'

    name = fields.Char(string='Name')
    client_id = fields.Char(
        string='Client ID',
        required=True,
        help="The OAuth Client ID obtained from the Zoho API Console.",copy=False
    )
    client_secret = fields.Char(
        string='Client Secret', required=True,
        help="The OAuth Client Secret obtained from the Zoho API Console.",copy=False)
    redirect_uri = fields.Char(
        string='Redirect URI',
        compute='_compute_redirect_uri',
        store=False,
        help="The callback URL that must be configured in your Zoho OAuth application"
    )
    account_id = fields.Char(
        string='Account ID', readonly=True,
        help="The unique Zoho Mail account ID retrieved after successful"
             " authentication.",copy=False)
    email_address = fields.Char(string='Email', readonly=True,
                                help="Zoho email address")
    refresh_token = fields.Text(
        string='Refresh Token', readonly=True,
        help="OAuth refresh token used to obtain new access tokens automatically.")
    access_token = fields.Text(
        string='Access Token', readonly=True,
        help="Temporary OAuth access token used to access the Zoho Mail API.")
    state = fields.Selection([
        ('draft', 'Not Connected'),
        ('connected', 'Connected'),
        ('error', 'Error')
    ], string='State', default='draft', help="Status of the Zoho mail account")
    inbox_folder_id = fields.Char(
        string='Inbox Folder',
        help="The Zoho Mail folder ID for the Inbox.")
    sent_folder_id = fields.Char(
        string='Sent Folder',
        help="The Zoho Mail folder ID for the Sent folder.")
    zoho_region = fields.Selection([
            ('com', 'United States (.com)'),
            ('in', 'India (.in)'),
            ('eu', 'Europe (.eu)'),
            ('com.au', 'Australia (.com.au)'),
            ('jp', 'Japan (.jp)'),
            ('com.cn', 'China (.com.cn)'),
        ], string="Zoho Region", required=True,
        help="Select the Zoho data center where your Zoho Mail account is hosted.")
    token_expiry = fields.Datetime(
        string='Token Expiry',
        help="Access Token Expiration date and time.")

    def _get_accounts_base_url(self):
        """Construct the base URL for Zoho Accounts services."""
        return f"https://accounts.zoho.{self.zoho_region}"

    def _get_mail_base_url(self):
        """Construct the base URL for Zoho Mail services."""
        return f"https://mail.zoho.{self.zoho_region}"

    def _compute_redirect_uri(self):
        """Compute the redirect URI for Zoho Mail services."""
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        for rec in self:
            rec.redirect_uri = (
                f"{base_url}/zoho_mail/oauth/callback"
            )

    def _get_valid_access_token(self):
        """Fetch the access token."""
        self.ensure_one()
        if (self.access_token and self.token_expiry
            and fields.Datetime.now() < self.token_expiry):
            return self.access_token
        return self._generate_access_token()

    def action_connect(self):
        """Connect to Zoho Mail services."""
        self.ensure_one()
        scopes = ",".join([
            "ZohoMail.accounts.READ",
            "ZohoMail.folders.READ",
            "ZohoMail.messages.READ",
            "ZohoMail.messages.ALL",
            "ZohoMail.messages.CREATE"
        ])
        params = {
            'scope': scopes,
            'client_id': self.client_id,
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent',
            'redirect_uri': self.redirect_uri,
            'state': str(self.id),
        }
        url = (
            f"{self._get_accounts_base_url()}/oauth/v2/auth?" + urlencode(params)
        )
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'self',
        }

    def _generate_access_token(self):
        """Generate an access token."""
        self.ensure_one()
        response = requests.post(
            f"{self._get_accounts_base_url()}/oauth/v2/token",
            data={
                'refresh_token': self.refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token',
            }, timeout=10
        )
        data = response.json()
        if response.status_code != 200:
            error_msg = data.get('error_message', 'Unknown error')
            _logger.error(f"API Error: {data}")
            raise UserError(_("Zoho API Error: %s") % error_msg)
        expires_in = data.get('expires_in', 3600)
        self.write({
            'access_token': data.get('access_token'),
            'token_expiry': (
                fields.Datetime.now() +
                datetime.timedelta(seconds=expires_in - 300)
            )
        })
        return self.access_token

    def test_connection(self):
        """Test the Zoho connection"""
        token = self.access_token
        if not token:
            token = self._generate_access_token()
        response = requests.get(
            f"{self._get_mail_base_url()}/api/accounts",
            headers={
                "Authorization":
                    f"Zoho-oauthtoken {token}"
            },
            timeout=10
        )
        data = response.json()
        if response.status_code != 200:
            raise UserError(_(str(data)))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Connection successful'),
                'type': 'success',
            }
        }

    def _headers(self, token):
        """Generate the authorization headers required for Zoho API requests."""
        token = self._get_valid_access_token()
        return {
            "Authorization": f"Zoho-oauthtoken {token}"
        }

    def _get_message_content(self, message_id, token):
        """Fetch the content of the Zoho mails"""
        headers = self._headers(token)
        response = (requests.get
            (
            f"{self._get_mail_base_url()}/api/accounts/"
            f"{self.account_id}/folders/"
            f"{self.inbox_folder_id}/messages/"
            f"{message_id}/content",
            headers=headers,
            timeout=10,
        ))
        data = response.json()
        return data.get('data', {}).get('content')

    def _get_inline_images(self, message_id, folder_id, content_id, token):
        """Download inline images from Zoho and replace their src with Odoo
        attachment URLs."""
        headers = self._headers(token)
        response = (requests.get
            (
            f"{self._get_mail_base_url()}/api/accounts/"
            f"{self.account_id}/folders/"
            f"{self.inbox_folder_id}/messages/"
            f"{message_id}/inline",
            headers=headers,
            params={'contentId': content_id,},
            timeout=10,
        ))
        return response

    def _get_message_attachments(self, message_id, token, mail):
        """Fetch the attachments of the Zoho mails"""
        headers = self._headers(token)
        response = (requests.get(
            f"{self._get_mail_base_url()}/api/accounts/"
            f"{self.account_id}/folders/"
            f"{self.inbox_folder_id}/messages/"
            f"{message_id}/attachmentinfo",
            headers=headers,
            timeout=10,
        ))
        attachment_data = response.json()
        attachment_ids = []
        for attachment in attachment_data.get(
            'data', {}).get('attachments', []):
            attachment_id = attachment['attachmentId']
            attachment_name = attachment['attachmentName']
            download_response = requests.get(
                f"{self._get_mail_base_url()}/api/accounts/"
                f"{self.account_id}/folders/"
                f"{self.inbox_folder_id}/messages/"
                f"{message_id}/attachments/"
                f"{attachment_id}",
                headers=headers,
                timeout=10,
            )
            if download_response.status_code != 200:
                continue
            ir_attachment = self.env['ir.attachment'].create({
                'name': attachment_name,
                'datas': base64.b64encode(download_response.content),
                'type': 'binary',
                'res_model': 'zoho.mail.message',
                'res_id': mail.id,
            })
            attachment_ids.append(ir_attachment.id)
        return attachment_ids

    def action_fetch_folders(self, token):
        """Retrieve all mail folders available in the authenticated
        Zoho Mail account."""
        self.ensure_one()
        headers = self._headers(token)
        response = requests.get(
            f"{self._get_mail_base_url()}/api/accounts/{self.account_id}/folders",
            headers=headers,
            timeout=10,
        )
        data = response.json()
        if response.status_code != 200:
            raise UserError(_(str(data)))
        inbox_id = False
        sent_id = False
        for folder in data.get('data', []):
            if folder.get('folderName') == 'Inbox':
                inbox_id = folder.get('folderId')
            elif folder.get('folderName') == 'Sent':
                sent_id = folder.get('folderId')
        self.write({
            'inbox_folder_id': inbox_id,
            'sent_folder_id': sent_id,                                                                                                                                              })

    def action_sync_inbox(self):
        """Sync the received Zoho emails"""
        self.ensure_one()
        token = self._generate_access_token()
        if not self.inbox_folder_id:
            self.action_fetch_folders(token)
        headers = self._headers(token)
        page_size = 50
        start_index = 1
        has_more = True
        total_synced = 0
        while has_more:
            try:
                response = requests.get(
                    f"{self._get_mail_base_url()}/api/accounts/{self.account_id}/messages/view",
                    headers=headers,
                    params={
                        'folderId': self.inbox_folder_id,
                        'limit': page_size,
                        'start': start_index,
                    },
                    timeout=10,
                )
                data = response.json()
                if response.status_code != 200:
                    raise UserError(_(str(data)))
                messages = data.get('data', [])
                if not isinstance(messages, list):
                    raise UserError(_(
                        "Unexpected response:\n%s") % data)
                mail_message_obj = self.env['zoho.mail.message']
                for message in messages:
                    message_id = message.get('messageId')
                    if not message_id:
                        continue
                    existing = mail_message_obj.search(
                        [('message_id', '=', message_id)],
                        limit=1
                    )
                    if existing:
                        continue
                    try:
                        body = self._get_message_content(message_id, token)
                        body = self._process_inline_images(
                            body, message_id, self.sent_folder_id, token
                        )
                        mail_record = mail_message_obj.create({
                            'message_id': message_id,
                            'subject': message.get('subject'),
                            'sender': message.get('fromAddress'),
                            'recipients': unescape(message.get('toAddress')),
                            'body': body,
                            'mail_type': 'inbox',
                            'date': datetime.datetime.fromtimestamp(
                                int(message['receivedTime']) / 1000),
                            'cc_address': message.get('ccAddress'),
                            'has_attachment': (
                                str(message.get('hasAttachment')) == '1'
                            ),
                        })
                        if str(message.get('hasAttachment')) == '1':
                            attachment_ids = (self._get_message_attachments(
                                message_id,token, mail_record))
                            mail_record.write({
                                'attachment_ids': [
                                    (6, 0, attachment_ids)
                                ]
                            })
                        total_synced += 1
                    except (requests.RequestException, ValueError, KeyError) as e:
                        _logger.warning(
                            f"Failed to sync message {message_id}: {str(e)}")
                        continue
                if len(messages) < page_size:
                    has_more = False
                else:
                    start_index += page_size
                    _logger.info(f"Synced {total_synced} emails, fetching next"
                                 f" batch...")
            except requests.Timeout:
                raise UserError(_(
                    "Request timeout while syncing. %s emails synced so far. "
                    "Try syncing again or increase timeout."
                ) % total_synced)
            except requests.RequestException as e:
                raise UserError(_(
                    "Network error during sync: %s. "
                    "%s emails synced so far."
                ) % (str(e), total_synced))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Inbox synced successfully'),
                'type': 'success',
            }
        }

    def action_sync_sent(self):
        """Sync the sent Zoho emails"""
        self.ensure_one()
        token = self._generate_access_token()
        if not self.sent_folder_id:
            self.action_fetch_folders(token)
        headers = self._headers(token)
        page_size = 50
        start_index = 1
        has_more = True
        total_synced = 0
        while has_more:
            try:
                response = requests.get(
                    f"{self._get_mail_base_url()}/api/accounts/"
                    f"{self.account_id}/messages/view",
                    headers=headers,
                    params={
                        "folderId": self.sent_folder_id,
                        "limit": page_size,
                        "start": start_index,
                    },
                    timeout=10,
                )
                data = response.json()
                if response.status_code != 200:
                    raise UserError(_(str(data)))
                messages = data.get('data', [])
                if not isinstance(messages, list):
                    raise UserError(_("Unexpected response:\n%s") % data)
                if not messages:
                    has_more = False
                    break
                for message in messages:
                    message_id = message.get('messageId')
                    if not message_id:
                        continue
                    existing = self.env['zoho.mail.message'].search(
                        [('message_id', '=', message_id)], limit=1)
                    if existing:
                        continue
                    try:
                        body = self._get_message_content(message_id, token)
                        body = self._process_inline_images(
                            body, message_id, message.get('folderId'), token
                        )
                        mail_record = self.env['zoho.mail.message'].create({
                            'message_id': message_id,
                            'subject': message.get('subject'),
                            'sender': message.get('fromAddress'),
                            'recipients': unescape(message.get('toAddress')),
                            'body': body,
                            'mail_type': 'sent',
                            'date': datetime.datetime.fromtimestamp(
                                int(message['receivedTime']) / 1000),
                            'has_attachment': (str(message.get(
                                'hasAttachment')) == '1')
                        })
                        if str(message.get('hasAttachment')) == '1':
                            attachment_ids = (self._get_message_attachments(
                                message_id,token, mail_record))
                            mail_record.write({
                                'attachment_ids': [
                                    (6, 0, attachment_ids)
                                ]
                            })
                        total_synced += 1
                    except Exception as e:
                        _logger.warning(f"Failed to sync message {message_id}: {str(e)}")
                        continue
                if len(messages) < page_size:
                    has_more = False
                else:
                    # Move to next batch
                    start_index += page_size
                    _logger.info(f"Synced {total_synced} emails, fetching next batch...")
            except requests.Timeout:
                raise UserError(_(
                    "Request timeout while syncing. %s emails synced so far. "
                    "Try syncing again or increase timeout."
                ) % total_synced)
            except requests.RequestException as e:
                raise UserError(_(
                    "Network error during sync: %s. "
                    "%s emails synced so far."
                ) % (str(e), total_synced))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Sent mails synced successfully'),
                'type': 'success',
            }
        }

    def send_mail(self, to_address, subject, body, cc_address=False,
                  bcc_address=False, attachments=None):
        """Send mails from Odoo using Zoho Mail account"""
        self.ensure_one()
        token = self._generate_access_token()
        headers = self._headers(token)
        zoho_attachment_ids = []
        uploaded_files = []
        if attachments:
            for attachment in attachments:
                file_content = base64.b64decode(attachment.datas)
                upload_response = requests.post(
                    f"{self._get_mail_base_url()}/api/accounts/"
                    f"{self.account_id}/messages/attachments",
                    headers=headers,
                    params={
                        'uploadType': 'multipart'
                    },
                    files=[
                        (
                            "attach",
                            (
                                attachment.name,
                                base64.b64decode(attachment.datas),
                                attachment.mimetype or
                                "application/octet-stream"
                            )
                        )
                    ],
                    timeout=30,
                )
                upload_data = upload_response.json()
                for file_data in upload_data['data']:
                    uploaded_files.append({
                        'storeName': file_data['storeName'],
                        'attachmentName': file_data['attachmentName'],
                        'attachmentPath': file_data['attachmentPath'],
                    })
                zoho_attachment_ids.append(upload_data.get('attachmentId'))
        token = self._get_valid_access_token()
        headers = {
            "Authorization":
                f"Zoho-oauthtoken {token}"
        }
        payload = {
            "fromAddress": self.email_address,
            "toAddress": to_address,
            "subject": subject,
            "content": body,
            "mailFormat": "html",
            "attachments": uploaded_files
        }
        if cc_address:
            payload['ccAddress'] = cc_address
        if bcc_address:
            payload['bccAddress'] = bcc_address
        response = requests.post(
            f"{self._get_mail_base_url()}"
            f"/api/accounts/{self.account_id}"
            f"/messages",
            headers=headers,
            json=payload,
            timeout=10
        )
        data = response.json()
        if response.status_code not in (200, 201):
            raise UserError(_(str(data)))
        return data

    def action_sync_all(self):
        """Synchronize sent and received emails through a scheduled cron job."""
        self.ensure_one()
        self.action_sync_inbox()
        self.action_sync_sent()

    @api.model
    def cron_sync_emails(self):
        """ Synchronize mailbox emails via cron. """
        accounts = self.search([
            ('state', '=', 'connected')
        ])
        for account in accounts:
            try:
                account.action_sync_all()
            except Exception:
                _logger.exception(
                    "Zoho sync failed for %s",
                    account.email_address
                )

    def _process_inline_images(
        self, body, message_id, token, folder_id, mail_type='inbox'):
        """Download inline images from Zoho and replace their src with Odoo
        attachment URLs."""
        if not body:
            return body
        soup = BeautifulSoup(body, 'html.parser')
        for img in soup.find_all('img'):
            src = img.get('src')
            query = parse_qs(urlparse(src).query)
            content_id = query.get('cid', [False])[0]
            if not content_id:
                continue
            if not src:
                continue
            response = self._get_inline_images(message_id, folder_id,
                content_id, token)
            attachment = self.env['ir.attachment'].create({
                'name': f'inline_{message_id}.png',
                'datas': base64.b64encode(response.content),
                'mimetype': response.headers.get('Content-Type'),
            })
            img['src'] = f"/web/content/{attachment.id}"
        return str(soup)
