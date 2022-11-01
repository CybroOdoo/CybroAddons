# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import odoo
from odoo.service import db
from odoo.http import request

import dropbox

from werkzeug import urls
from datetime import timedelta

import datetime
import os
import paramiko
import ftplib
import json
import requests
import tempfile
import errno
import logging

_logger = logging.getLogger(__name__)

ONEDRIVE_SCOPE = ['offline_access openid Files.ReadWrite.All']
MICROSOFT_GRAPH_END_POINT = "https://graph.microsoft.com"
GOOGLE_AUTH_ENDPOINT = 'https://accounts.google.com/o/oauth2/auth'
GOOGLE_TOKEN_ENDPOINT = 'https://accounts.google.com/o/oauth2/token'
GOOGLE_API_BASE_URL = 'https://www.googleapis.com'


class AutoDatabaseBackup(models.Model):
    _name = 'db.backup.configure'
    _description = 'Automatic Database Backup'

    name = fields.Char(string='Name', required=True)
    db_name = fields.Char(string='Database Name', required=True)
    master_pwd = fields.Char(string='Master Password', required=True)
    backup_format = fields.Selection([
        ('zip', 'Zip'),
        ('dump', 'Dump')
    ], string='Backup Format', default='zip', required=True)
    backup_destination = fields.Selection([
        ('local', 'Local Storage'),
        ('google_drive', 'Google Drive'),
        ('ftp', 'FTP'),
        ('sftp', 'SFTP'),
        ('dropbox', 'Dropbox'),
        ('onedrive', 'Onedrive')
    ], string='Backup Destination')
    backup_path = fields.Char(string='Backup Path', help='Local storage directory path')
    sftp_host = fields.Char(string='SFTP Host')
    sftp_port = fields.Char(string='SFTP Port', default=22)
    sftp_user = fields.Char(string='SFTP User', copy=False)
    sftp_password = fields.Char(string='SFTP Password', copy=False)
    sftp_path = fields.Char(string='SFTP Path')
    ftp_host = fields.Char(string='FTP Host')
    ftp_port = fields.Char(string='FTP Port', default=21)
    ftp_user = fields.Char(string='FTP User', copy=False)
    ftp_password = fields.Char(string='FTP Password', copy=False)
    ftp_path = fields.Char(string='FTP Path')
    dropbox_client_id = fields.Char(string='Dropbox Client ID', copy=False)
    dropbox_client_secret = fields.Char(string='Dropbox Client Secret', copy=False)
    dropbox_refresh_token = fields.Char(string='Dropbox Refresh Token', copy=False)
    is_dropbox_token_generated = fields.Boolean(string='Dropbox Token Generated', compute='_compute_is_dropbox_token_generated', copy=False)
    dropbox_folder = fields.Char('Dropbox Folder')
    active = fields.Boolean(default=True)
    auto_remove = fields.Boolean(string='Remove Old Backups')
    days_to_remove = fields.Integer(string='Remove After',
                                    help='Automatically delete stored backups after this specified number of days')
    google_drive_folderid = fields.Char(string='Drive Folder ID')
    notify_user = fields.Boolean(string='Notify User',
                                 help='Send an email notification to user when the backup operation is successful or failed')
    user_id = fields.Many2one('res.users', string='User')
    backup_filename = fields.Char(string='Backup Filename', help='For Storing generated backup filename')
    generated_exception = fields.Char(string='Exception', help='Exception Encountered while Backup generation')
    onedrive_client_id = fields.Char(string='Onedrive Client ID', copy=False)
    onedrive_client_secret = fields.Char(string='Onedrive Client Secret', copy=False)
    onedrive_access_token = fields.Char(string='Onedrive Access Token', copy=False)
    onedrive_refresh_token = fields.Char(string='Onedrive Refresh Token', copy=False)
    onedrive_token_validity = fields.Datetime(string='Onedrive Token Validity', copy=False)
    onedrive_folder_id = fields.Char(string='Folder ID')
    is_onedrive_token_generated = fields.Boolean(string='onedrive Tokens Generated',
                                                compute='_compute_is_onedrive_token_generated', copy=False)
    gdrive_refresh_token = fields.Char(string='Google drive Refresh Token', copy=False)
    gdrive_access_token = fields.Char(string='Google Drive Access Token', copy=False)
    is_google_drive_token_generated = fields.Boolean(string='Google drive Token Generated',
                                                     compute='_compute_is_google_drive_token_generated', copy=False)
    gdrive_client_id = fields.Char(string='Google Drive Client ID', copy=False)
    gdrive_client_secret = fields.Char(string='Google Drive Client Secret', copy=False)
    gdrive_token_validity = fields.Datetime(string='Google Drive Token Validity', copy=False)
    onedrive_redirect_uri = fields.Char(string='Onedrive Redirect URI', compute='_compute_redirect_uri')
    gdrive_redirect_uri = fields.Char(string='Google Drive Redirect URI', compute='_compute_redirect_uri')

    def _compute_redirect_uri(self):
        for rec in self:
            base_url = request.env['ir.config_parameter'].get_param('web.base.url')
            rec.onedrive_redirect_uri = base_url + '/onedrive/authentication'
            rec.gdrive_redirect_uri = base_url + '/google_drive/authentication'

    @api.depends('onedrive_access_token', 'onedrive_refresh_token')
    def _compute_is_onedrive_token_generated(self):
        """
        Set true if onedrive tokens are generated
        """
        for rec in self:
            rec.is_onedrive_token_generated = bool(rec.onedrive_access_token) and bool(rec.onedrive_refresh_token)

    @api.depends('dropbox_refresh_token')
    def _compute_is_dropbox_token_generated(self):
        """
        Set True if the dropbox refresh token is generated
        """
        for rec in self:
            rec.is_dropbox_token_generated = bool(rec.dropbox_refresh_token)

    @api.depends('gdrive_access_token', 'gdrive_refresh_token')
    def _compute_is_google_drive_token_generated(self):
        """
        Set True if the Google Drive refresh token is generated
        """
        for rec in self:
            rec.is_google_drive_token_generated = bool(rec.gdrive_access_token) and bool(rec.gdrive_refresh_token)

    def action_get_dropbox_auth_code(self):
        """
        Open a wizard to set up dropbox Authorization code
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dropbox Authorization Wizard',
            'res_model': 'authentication.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'dropbox_auth': True}
        }

    def action_get_onedrive_auth_code(self):
        """
        Generate onedrive authorization code
        """
        AUTHORITY = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
        action = self.env["ir.actions.act_window"].sudo()._for_xml_id("auto_database_backup.action_db_backup_configure")
        base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        url_return = base_url + '/web#id=%d&action=%d&view_type=form&model=%s' % (self.id, action['id'], 'db.backup.configure')
        state = {
            'backup_config_id': self.id,
            'url_return': url_return
        }
        encoded_params = urls.url_encode({
            'response_type': 'code',
            'client_id': self.onedrive_client_id,
            'state': json.dumps(state),
            'scope': ONEDRIVE_SCOPE,
            'redirect_uri': base_url + '/onedrive/authentication',
            'prompt': 'consent',
            'access_type': 'offline'
        })
        auth_url = "%s?%s" % (AUTHORITY, encoded_params)
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': auth_url,
        }

    def action_get_gdrive_auth_code(self):
        """
        Generate ogoogle drive authorization code
        """
        action = self.env["ir.actions.act_window"].sudo()._for_xml_id("auto_database_backup.action_db_backup_configure")
        base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        url_return = base_url + '/web#id=%d&action=%d&view_type=form&model=%s' % (self.id, action['id'], 'db.backup.configure')
        state = {
            'backup_config_id': self.id,
            'url_return': url_return
        }
        encoded_params = urls.url_encode({
            'response_type': 'code',
            'client_id': self.gdrive_client_id,
            'scope': 'https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/drive.file',
            'redirect_uri': base_url + '/google_drive/authentication',
            'access_type': 'offline',
            'state': json.dumps(state),
            'approval_prompt': 'force',
        })
        auth_url = "%s?%s" % (GOOGLE_AUTH_ENDPOINT, encoded_params)
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': auth_url,
        }

    def generate_onedrive_refresh_token(self):
        """
        generate onedrive access token from refresh token if expired
        """
        base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        data = {
            'client_id': self.onedrive_client_id,
            'client_secret': self.onedrive_client_secret,
            'scope': ONEDRIVE_SCOPE,
            'grant_type': "refresh_token",
            'redirect_uri': base_url + '/onedrive/authentication',
            'refresh_token': self.onedrive_refresh_token
        }
        try:
            res = requests.post("https://login.microsoftonline.com/common/oauth2/v2.0/token", data=data, headers=headers)
            res.raise_for_status()
            response = res.content and res.json() or {}
            if response:
                expires_in = response.get('expires_in')
                self.write({
                    'onedrive_access_token': response.get('access_token'),
                    'onedrive_refresh_token': response.get('refresh_token'),
                    'onedrive_token_validity': fields.Datetime.now() + timedelta(seconds=expires_in) if expires_in else False,
                })
        except requests.HTTPError as error:
            _logger.exception("Bad microsoft onedrive request : %s !", error.response.content)
            raise error

    def get_onedrive_tokens(self, authorize_code):
        """
        Generate onedrive tokens from authorization code
        """
        headers = {"content-type": "application/x-www-form-urlencoded"}
        base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        data = {
            'code': authorize_code,
            'client_id': self.onedrive_client_id,
            'client_secret': self.onedrive_client_secret,
            'grant_type': 'authorization_code',
            'scope': ONEDRIVE_SCOPE,
            'redirect_uri': base_url + '/onedrive/authentication'
        }
        try:
            res = requests.post("https://login.microsoftonline.com/common/oauth2/v2.0/token", data=data, headers=headers)
            res.raise_for_status()
            response = res.content and res.json() or {}
            if response:
                expires_in = response.get('expires_in')
                self.write({
                    'onedrive_access_token': response.get('access_token'),
                    'onedrive_refresh_token': response.get('refresh_token'),
                    'onedrive_token_validity': fields.Datetime.now() + timedelta(seconds=expires_in) if expires_in else False,
                })
        except requests.HTTPError as error:
            _logger.exception("Bad microsoft onedrive request : %s !", error.response.content)
            raise error

    def generate_gdrive_refresh_token(self):
        """
        generate google drive access token from refresh token if expired
        """
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            'refresh_token': self.gdrive_refresh_token,
            'client_id': self.gdrive_client_id,
            'client_secret': self.gdrive_client_secret,
            'grant_type': 'refresh_token',
        }
        try:
            res = requests.post(GOOGLE_TOKEN_ENDPOINT, data=data, headers=headers)
            res.raise_for_status()
            response = res.content and res.json() or {}
            if response:
                expires_in = response.get('expires_in')
                self.write({
                    'gdrive_access_token': response.get('access_token'),
                    'gdrive_token_validity': fields.Datetime.now() + timedelta(seconds=expires_in) if expires_in else False,
                })
        except requests.HTTPError as error:
            error_key = error.response.json().get("error", "nc")
            error_msg = _(
                "An error occurred while generating the token. Your authorization code may be invalid or has already expired [%s]. "
                "You should check your Client ID and secret on the Google APIs plateform or try to stop and restart your calendar synchronisation.",
                error_key)
            raise UserError(error_msg)

    def get_gdrive_tokens(self, authorize_code):
        """
        Generate onedrive tokens from authorization code
        """

        base_url = request.env['ir.config_parameter'].get_param('web.base.url')

        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            'code': authorize_code,
            'client_id': self.gdrive_client_id,
            'client_secret': self.gdrive_client_secret,
            'grant_type': 'authorization_code',
            'redirect_uri': base_url + '/google_drive/authentication'
        }
        try:
            res = requests.post(GOOGLE_TOKEN_ENDPOINT, params=data,
                                headers=headers)
            res.raise_for_status()
            response = res.content and res.json() or {}
            if response:
                expires_in = response.get('expires_in')
                self.write({
                    'gdrive_access_token': response.get('access_token'),
                    'gdrive_refresh_token': response.get('refresh_token'),
                    'gdrive_token_validity': fields.Datetime.now() + timedelta(
                        seconds=expires_in) if expires_in else False,
                })
        except requests.HTTPError:
            error_msg = _("Something went wrong during your token generation. Maybe your Authorization Code is invalid")
            raise UserError(error_msg)

    def get_dropbox_auth_url(self):
        """
        Return dropbox authorization url
        """
        dbx_auth = dropbox.oauth.DropboxOAuth2FlowNoRedirect(self.dropbox_client_id, self.dropbox_client_secret,
                                                             token_access_type='offline')
        auth_url = dbx_auth.start()
        return auth_url

    def set_dropbox_refresh_token(self, auth_code):
        """
        Generate and set the dropbox refresh token from authorization code

        """
        dbx_auth = dropbox.oauth.DropboxOAuth2FlowNoRedirect(self.dropbox_client_id, self.dropbox_client_secret,
                                                             token_access_type='offline')
        outh_result = dbx_auth.finish(auth_code)
        self.dropbox_refresh_token = outh_result.refresh_token

    @api.constrains('db_name')
    def _check_db_credentials(self):
        """
        Validate entered database name and master password
        """
        database_list = db.list_dbs()
        if self.db_name not in database_list:
            raise ValidationError(_("Invalid Database Name!"))
        try:
            odoo.service.db.check_super(self.master_pwd)
        except Exception:
            raise ValidationError(_("Invalid Master Password!"))

    def test_connection(self):
        """
        Test the sftp and ftp connection using entered credentials
        """
        if self.backup_destination == 'sftp':
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(hostname=self.sftp_host, username=self.sftp_user, password=self.sftp_password, port=self.sftp_port)
                sftp = client.open_sftp()
                sftp.close()
            except Exception as e:
                raise UserError(_("SFTP Exception: %s", e))
            finally:
                client.close()
        elif self.backup_destination == 'ftp':
            try:
                ftp_server = ftplib.FTP()
                ftp_server.connect(self.ftp_host, int(self.ftp_port))
                ftp_server.login(self.ftp_user, self.ftp_password)
                ftp_server.quit()
            except Exception as e:
                raise UserError(_("FTP Exception: %s", e))
        title = _("Connection Test Succeeded!")
        message = _("Everything seems properly set up!")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'sticky': False,
            }
        }

    def _schedule_auto_backup(self):
        """
        Function for generating and storing backup
        Database backup for all the active records in backup configuration model will be created
        """
        records = self.search([])
        mail_template_success = self.env.ref('auto_database_backup.mail_template_data_db_backup_successful')
        mail_template_failed = self.env.ref('auto_database_backup.mail_template_data_db_backup_failed')
        for rec in records:
            backup_time = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
            backup_filename = "%s_%s.%s" % (rec.db_name, backup_time, rec.backup_format)
            rec.backup_filename = backup_filename
            # Local backup
            if rec.backup_destination == 'local':
                try:
                    if not os.path.isdir(rec.backup_path):
                        os.makedirs(rec.backup_path)
                    backup_file = os.path.join(rec.backup_path, backup_filename)
                    f = open(backup_file, "wb")
                    odoo.service.db.dump_db(rec.db_name, f, rec.backup_format)
                    f.close()
                    # remove older backups
                    if rec.auto_remove:
                        for filename in os.listdir(rec.backup_path):
                            file = os.path.join(rec.backup_path, filename)
                            create_time = datetime.datetime.fromtimestamp(os.path.getctime(file))
                            backup_duration = datetime.datetime.utcnow() - create_time
                            if backup_duration.days >= rec.days_to_remove:
                                os.remove(file)
                    if rec.notify_user:
                        mail_template_success.send_mail(rec.id, force_send=True)
                except Exception as e:
                    rec.generated_exception = e
                    _logger.info('FTP Exception: %s', e)
                    if rec.notify_user:
                        mail_template_failed.send_mail(rec.id, force_send=True)
            # FTP backup
            elif rec.backup_destination == 'ftp':
                try:
                    ftp_server = ftplib.FTP()
                    ftp_server.connect(rec.ftp_host, int(rec.ftp_port))
                    ftp_server.login(rec.ftp_user, rec.ftp_password)
                    ftp_server.encoding = "utf-8"
                    temp = tempfile.NamedTemporaryFile(suffix='.%s' % rec.backup_format)
                    try:
                        ftp_server.cwd(rec.ftp_path)
                    except ftplib.error_perm:
                        ftp_server.mkd(rec.ftp_path)
                        ftp_server.cwd(rec.ftp_path)
                    with open(temp.name, "wb+") as tmp:
                        odoo.service.db.dump_db(rec.db_name, tmp, rec.backup_format)
                    ftp_server.storbinary('STOR %s' % backup_filename, open(temp.name, "rb"))
                    if rec.auto_remove:
                        files = ftp_server.nlst()
                        for f in files:
                            create_time = datetime.datetime.strptime(ftp_server.sendcmd('MDTM ' + f)[4:], "%Y%m%d%H%M%S")
                            diff_days = (datetime.datetime.now() - create_time).days
                            if diff_days >= rec.days_to_remove:
                                ftp_server.delete(f)
                    ftp_server.quit()
                    if rec.notify_user:
                        mail_template_success.send_mail(rec.id, force_send=True)
                except Exception as e:
                    rec.generated_exception = e
                    _logger.info('FTP Exception: %s', e)
                    if rec.notify_user:
                        mail_template_failed.send_mail(rec.id, force_send=True)
            # SFTP backup
            elif rec.backup_destination == 'sftp':
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                try:
                    client.connect(hostname=rec.sftp_host, username=rec.sftp_user, password=rec.sftp_password, port=rec.sftp_port)
                    sftp = client.open_sftp()
                    temp = tempfile.NamedTemporaryFile(suffix='.%s' % rec.backup_format)
                    with open(temp.name, "wb+") as tmp:
                        odoo.service.db.dump_db(rec.db_name, tmp, rec.backup_format)
                    try:
                        sftp.chdir(rec.sftp_path)
                    except IOError as e:
                        if e.errno == errno.ENOENT:
                            sftp.mkdir(rec.sftp_path)
                            sftp.chdir(rec.sftp_path)
                    sftp.put(temp.name, backup_filename)
                    if rec.auto_remove:
                        files = sftp.listdir()
                        expired = list(filter(lambda fl: (datetime.datetime.now() - datetime.datetime.fromtimestamp(sftp.stat(fl).st_mtime)).days >= rec.days_to_remove, files))
                        for file in expired:
                            sftp.unlink(file)
                    sftp.close()
                    if rec.notify_user:
                        mail_template_success.send_mail(rec.id, force_send=True)
                except Exception as e:
                    rec.generated_exception = e
                    _logger.info('SFTP Exception: %s', e)
                    if rec.notify_user:
                        mail_template_failed.send_mail(rec.id, force_send=True)
                finally:
                    client.close()
            # Google Drive backup
            elif rec.backup_destination == 'google_drive':
                if rec.gdrive_token_validity <= fields.Datetime.now():
                    rec.generate_gdrive_refresh_token()
                temp = tempfile.NamedTemporaryFile(suffix='.%s' % rec.backup_format)
                with open(temp.name, "wb+") as tmp:
                    odoo.service.db.dump_db(rec.db_name, tmp, rec.backup_format)
                try:
                    # access_token = self.env['google.drive.config'].sudo().get_access_token()
                    headers = {"Authorization": "Bearer %s" % rec.gdrive_access_token}
                    para = {
                        "name": backup_filename,
                        "parents": [rec.google_drive_folderid],
                    }
                    files = {
                        'data': ('metadata', json.dumps(para), 'application/json; charset=UTF-8'),
                        'file': open(temp.name, "rb")
                    }
                    requests.post(
                        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
                        headers=headers,
                        files=files
                    )
                    if rec.auto_remove:
                        query = "parents = '%s'" % rec.google_drive_folderid
                        files_req = requests.get("https://www.googleapis.com/drive/v3/files?q=%s" % query, headers=headers)
                        files = files_req.json()['files']
                        for file in files:
                            file_date_req = requests.get("https://www.googleapis.com/drive/v3/files/%s?fields=createdTime" % file['id'], headers=headers)
                            create_time = file_date_req.json()['createdTime'][:19].replace('T', ' ')
                            diff_days = (datetime.datetime.now() - datetime.datetime.strptime(create_time, '%Y-%m-%d %H:%M:%S')).days
                            if diff_days >= rec.days_to_remove:
                                requests.delete("https://www.googleapis.com/drive/v3/files/%s" % file['id'], headers=headers)
                    if rec.notify_user:
                        mail_template_success.send_mail(rec.id, force_send=True)
                except Exception as e:
                    rec.generated_exception = e
                    _logger.info('Google Drive Exception: %s', e)
                    if rec.notify_user:
                        mail_template_failed.send_mail(rec.id, force_send=True)
            # Dropbox backup
            elif rec.backup_destination == 'dropbox':
                temp = tempfile.NamedTemporaryFile(suffix='.%s' % rec.backup_format)
                with open(temp.name, "wb+") as tmp:
                    odoo.service.db.dump_db(rec.db_name, tmp, rec.backup_format)
                try:
                    dbx = dropbox.Dropbox(app_key=rec.dropbox_client_id, app_secret=rec.dropbox_client_secret, oauth2_refresh_token=rec.dropbox_refresh_token)
                    dropbox_destination = rec.dropbox_folder + '/' + backup_filename
                    dbx.files_upload(temp.read(), dropbox_destination)
                    if rec.auto_remove:
                        files = dbx.files_list_folder(rec.dropbox_folder)
                        file_entries = files.entries
                        expired_files = list(filter(lambda fl: (datetime.datetime.now() - fl.client_modified).days >= rec.days_to_remove, file_entries))
                        for file in expired_files:
                            dbx.files_delete_v2(file.path_display)
                    if rec.notify_user:
                        mail_template_success.send_mail(rec.id, force_send=True)
                except Exception as error:
                    rec.generated_exception = error
                    _logger.info('Dropbox Exception: %s', error)
                    if rec.notify_user:
                        mail_template_failed.send_mail(rec.id, force_send=True)
            # Onedrive Backup
            elif rec.backup_destination == 'onedrive':
                if rec.onedrive_token_validity <= fields.Datetime.now():
                    rec.generate_onedrive_refresh_token()
                temp = tempfile.NamedTemporaryFile(suffix='.%s' % rec.backup_format)
                with open(temp.name, "wb+") as tmp:
                    odoo.service.db.dump_db(rec.db_name, tmp, rec.backup_format)
                headers = {'Authorization': 'Bearer %s' % rec.onedrive_access_token, 'Content-Type': 'application/json'}
                upload_session_url = MICROSOFT_GRAPH_END_POINT + "/v1.0/me/drive/items/%s:/%s:/createUploadSession" % (rec.onedrive_folder_id, backup_filename)
                try:
                    upload_session = requests.post(upload_session_url, headers=headers)
                    upload_url = upload_session.json().get('uploadUrl')
                    requests.put(upload_url, data=temp.read())
                    if rec.auto_remove:
                        list_url = MICROSOFT_GRAPH_END_POINT + "/v1.0/me/drive/items/%s/children" % rec.onedrive_folder_id
                        response = requests.get(list_url, headers=headers)
                        files = response.json().get('value')
                        for file in files:
                            create_time = file['createdDateTime'][:19].replace('T', ' ')
                            diff_days = (datetime.datetime.now() - datetime.datetime.strptime(create_time, '%Y-%m-%d %H:%M:%S')).days
                            if diff_days >= rec.days_to_remove:
                                delete_url = MICROSOFT_GRAPH_END_POINT + "/v1.0/me/drive/items/%s" % file['id']
                                requests.delete(delete_url, headers=headers)
                    if rec.notify_user:
                        mail_template_success.send_mail(rec.id, force_send=True)
                except Exception as error:
                    rec.generated_exception = error
                    _logger.info('Onedrive Exception: %s', error)
                    if rec.notify_user:
                        mail_template_failed.send_mail(rec.id, force_send=True)
