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
import json
import logging
from datetime import timedelta
import requests
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class OneDriveDashboard(models.Model):
    """
    Generate refresh and  access token
    """
    _name = 'onedrive.dashboard'
    _description = "Generate access and refresh tokens "

    onedrive_access_token = fields.Char(
        string="OneDrive Access Token",
        store=True,
        help="Access token for authenticating and accessing OneDrive APIs.")
    onedrive_refresh_token = fields.Char(
        string="OneDrive Refresh Token",
        help="Refresh token for obtaining a new access token when the current "
             "one expires.")
    token_expiry_date = fields.Datetime(
        string="OneDrive Token Validity",
        help="Validity period of the access token, indicating until when it is"
             " valid.")
    upload_file = fields.Binary(
        string="Upload File",
        help="Binary field to store the uploaded file.")

    def get_tokens(self, authorize_code):
        """
        Generate onedrive tokens from authorization code
        """
        ir_config = self.env['ir.config_parameter'].sudo()
        data = {
            'code': authorize_code,
            'client_id': ir_config.get_str(
                'onedrive_integration_odoo.client_id', ''),
            'client_secret': ir_config.get_str(
                'onedrive_integration_odoo.client_secret', ''),
            'grant_type': 'authorization_code',
            'scope': ['offline_access openid Files.ReadWrite.All'],
            'redirect_uri': ir_config.get_str(
                'web.base.url', '') + '/onedrive/authentication'
        }
        try:
            res = requests.post(
                "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                data=data,
                headers={"content-type": "application/x-www-form-urlencoded"},
                timeout=10)
            res.raise_for_status()
            response = res.content and res.json() or {}
            if response:
                expires_in = response.get('expires_in')
                access_token = response.get('access_token')
                refresh_token = response.get('refresh_token')
                token_expiry_date = fields.Datetime.now() + timedelta(
                    seconds=expires_in) if expires_in else False
                if access_token:
                    self.env['onedrive.dashboard'].create([{
                        'onedrive_access_token': access_token,
                        'onedrive_refresh_token': refresh_token,
                        'token_expiry_date': token_expiry_date,
                    }])
        except requests.HTTPError as error:
            _logger.exception("Bad microsoft onedrive request : %s !",
                              error.response.content)
            raise error

    def generate_onedrive_refresh_token(self):
        """
        Generate onedrive access token from refresh token if expired
        """
        self.ensure_one()
        if not self.onedrive_refresh_token:
            return False
        ir_config = self.env['ir.config_parameter'].sudo()
        data = {
            'client_id': ir_config.get_str(
                'onedrive_integration_odoo.client_id', ''),
            'client_secret': ir_config.get_str(
                'onedrive_integration_odoo.client_secret', ''),
            'scope': ['offline_access openid Files.ReadWrite.All'],
            'grant_type': "refresh_token",
            'redirect_uri': ir_config.get_str(
                'web.base.url', '') + '/onedrive/authentication',
            'refresh_token': self.onedrive_refresh_token
        }
        try:
            res = requests.post(
                "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                data=data,
                headers={"Content-type": "application/x-www-form-urlencoded"},
                timeout=10)
            res.raise_for_status()
            response = res.content and res.json() or {}
            if response:
                expires_in = response.get('expires_in')
                self.write({
                    'onedrive_access_token': response.get('access_token'),
                    'onedrive_refresh_token': response.get('refresh_token'),
                    'token_expiry_date': fields.Datetime.now() + timedelta(
                        seconds=expires_in) if expires_in else False,
                })
        except requests.HTTPError as error:
            _logger.exception("Bad microsoft onedrive request : %s !",
                              error.response.content)
            raise error

    @api.model
    def action_synchronize_onedrive(self):
        """
        Pass the files to JavaScript
        """
        record = self.search([], order='id desc', limit=1)
        if not record or (not record.onedrive_access_token and not record.onedrive_refresh_token):
            return False
        if not record.token_expiry_date or record.token_expiry_date <= fields.Datetime.now():
            if record.onedrive_refresh_token:
                record.generate_onedrive_refresh_token()
            else:
                return False
        folder = self.env['ir.config_parameter'].sudo().get_str(
            'onedrive_integration_odoo.onedrive_folder', '')
        if not folder:
            return False
        url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{folder}:/children"
        headers = {
            'Authorization': f'Bearer {record.onedrive_access_token}',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            message = json.loads(response.content) if response.content else {}
        except Exception as e:
            _logger.exception("OneDrive sync request failed: %s", e)
            return ['error', 'connectionError', str(e)]

        if 'error' in message:
            return ['error', message['error'].get('code', 'error'),
                    message['error'].get('message', 'Unknown error')]
        files = {}
        for file in message.get('value', []):
            if '@microsoft.graph.downloadUrl' in file and 'name' in file:
                files[file['name']] = file['@microsoft.graph.downloadUrl']
        return files
