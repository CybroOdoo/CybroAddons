# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, fields, models, _
import datetime

from odoo.http import request
from odoo.service import db
from datetime import timedelta
import boto3
import errno
import dropbox
import ftplib
import json
import logging
import nextcloud_client
import odoo
import os
import paramiko
import requests
from nextcloud import NextCloud
from requests.auth import HTTPBasicAuth
import tempfile
from werkzeug import urls
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
ONEDRIVE_SCOPE = ['offline_access openid Files.ReadWrite.All']
MICROSOFT_GRAPH_END_POINT = "https://graph.microsoft.com"
GOOGLE_AUTH_ENDPOINT = 'https://accounts.google.com/o/oauth2/auth'
GOOGLE_TOKEN_ENDPOINT = 'https://accounts.google.com/o/oauth2/token'
GOOGLE_API_BASE_URL = 'https://www.googleapis.com'


class DbBackupConfigure(models.Model):
    """Model for database backup configuration and backup functions"""
    _name = 'db.backup.configure'
    _description = 'Db Backup Configure'

    name = fields.Char(string='Name', required=True,
                       help='Name of the backup configuration')
    db_name = fields.Char(string='Database Name', required=True,
                          help='Name of the database')
    master_pwd = fields.Char(string='Master Password', required=True,
                             help='Master password of the database')
    backup_format = fields.Selection([
        ('zip', 'Zip'),
        ('dump', 'Dump')
    ], string='Backup Format', default='zip', required=True,
        help='Backup Format')
    backup_destination = fields.Selection([
        ('local', 'Local Storage'),
        ('google_drive', 'Google Drive'),
        ('ftp', 'FTP'),
        ('sftp', 'SFTP'),
        ('dropbox', 'Dropbox'),
        ('onedrive', 'Onedrive'),
        ('next_cloud', 'Next Cloud'),
        ('amazon_s3', 'Amazon S3')
    ], string='Backup Destination',
        help='Specify the location that the backup need to store')
    backup_path = fields.Char(string='Backup Path',
                              help='Local storage directory path')
    sftp_host = fields.Char(string='SFTP Host', help='SFTP Host Name')
    sftp_port = fields.Char(string='SFTP Port', default=22, help='SFTP Port')
    sftp_user = fields.Char(string='SFTP User', help='SFTP user name')
    sftp_password = fields.Char(string='SFTP Password', help='SFTP Password')
    sftp_path = fields.Char(string='SFTP Path', help='SFTP Path')
    ftp_host = fields.Char(string='FTP Host', help='FTP Host Name')
    ftp_port = fields.Char(string='FTP Port', default=21, help='FTP Port')
    ftp_user = fields.Char(string='FTP User', help='FTP User')
    ftp_password = fields.Char(string='FTP Password', help='FTP password')
    ftp_path = fields.Char(string='FTP Path', help='FTP Path')
    dropbox_client_key = fields.Char(string='Dropbox Client ID', copy=False,
                                     help='Client id of the dropbox')
    dropbox_client_secret = fields.Char(string='Dropbox Client Secret',
                                        copy=False,
                                        help='Client secret id of the dropbox')
    dropbox_refresh_token = fields.Char(string='Dropbox Refresh Token',
                                        copy=False,
                                        help='Refresh token for the dropbox')
    is_dropbox_token_generated = fields.Boolean(
        string='Dropbox Token Generated',
        compute='_compute_is_dropbox_token_generated',
        copy=False, help='Is the dropbox token generated or not?')
    dropbox_folder = fields.Char(string='Dropbox Folder', help='Dropbox folder')
    active = fields.Boolean(default=True, help='Checking the configuration'
                                               ' is active or not')
    save_to_drive = fields.Boolean(help='Checking whether the backup need '
                                        'to store in drive')
    auto_remove = fields.Boolean(string='Remove Old Backups',
                                 help='Remove Old Backups')
    days_to_remove = fields.Integer(string='Remove After',
                                    help='Automatically delete stored backups '
                                         'after this specified number of days')
    google_drive_folder = fields.Char(string='Drive Folder ID')
    notify_user = fields.Boolean(string='Notify User',
                                 help='Send an email notification to user when '
                                      'the backup operation is successful or '
                                      'failed')
    user_id = fields.Many2one('res.users', string='User')
    backup_filename = fields.Char(string='Backup Filename',
                                  help='For Storing generated backup filename')
    generated_exception = fields.Char(string='Exception',
                                      help='Exception Encountered while Backup '
                                           'generation')
    gdrive_refresh_token = fields.Char(string='Google drive Refresh Token',
                                       copy=False,
                                       help='Refresh token for google drive')
    gdrive_access_token = fields.Char(string='Google Drive Access Token',
                                      copy=False,
                                      help='Access token for google drive')
    is_google_drive_token_generated = fields.Boolean(
        string='Google drive Token Generated',
        compute='_compute_is_google_drive_token_generated', copy=False,
        help='Google drive token generated or not')
    gdrive_client_key = fields.Char(string='Google Drive Client ID', copy=False,
                                    help='Client id of the google drive')
    gdrive_client_secret = fields.Char(string='Google Drive Client Secret',
                                       copy=False,
                                       help='Client secret id of the google'
                                            ' drive')
    gdrive_token_validity = fields.Datetime(
        string='Google Drive Token Validity', copy=False,
        help='Token validity of the google drive')
    gdrive_redirect_uri = fields.Char(string='Google Drive Redirect URI',
                                      compute='_compute_redirect_uri',
                                      help='Redirect URI of the google drive')
    domain = fields.Char(string='Domain Name', help="Field used to store the "
                                                    "name of a domain")
    next_cloud_user_name = fields.Char(string='User Name',
                                       help="Field used to store the user name"
                                            " for a Nextcloud account.")
    next_cloud_password = fields.Char(string='Password',
                                      help="Field used to store the password"
                                           " for a Nextcloud account.")
    nextcloud_folder_key = fields.Char(string='Next Cloud Folder Id',
                                       help="Field used to store the unique "
                                            "identifier for a Nextcloud "
                                            "folder.")
    onedrive_client_key = fields.Char(string='Onedrive Client ID', copy=False,
                                      help='Client ID of the onedrive')
    onedrive_client_secret = fields.Char(string='Onedrive Client Secret',
                                         copy=False, help='Client secret id of'
                                                          ' the onedrive')
    onedrive_access_token = fields.Char(string='Onedrive Access Token',
                                        copy=False,
                                        help='Access token for one drive')
    onedrive_refresh_token = fields.Char(string='Onedrive Refresh Token',
                                         copy=False,
                                         help='Refresh token for one drive')
    onedrive_token_validity = fields.Datetime(string='Onedrive Token Validity',
                                              copy=False,
                                              help='Token validity date')
    onedrive_folder_key = fields.Char(string='Folder ID',
                                      help='Folder id of the onedrive')
    is_onedrive_token_generated = fields.Boolean(
        string='onedrive Tokens Generated',
        compute='_compute_is_onedrive_token_generated',
        copy=False, help='Whether to generate onedrive token?')
    onedrive_redirect_uri = fields.Char(string='Onedrive Redirect URI',
                                        compute='_compute_redirect_uri',
                                        help='Redirect URI of the onedrive')
    aws_access_key = fields.Char(string="Amazon S3 Access Key",
                                 help="Field used to store the Access Key"
                                      " for an Amazon S3 bucket.")
    aws_secret_access_key = fields.Char(string='Amazon S3 Secret Key',
                                        help="Field used to store the Secret"
                                             " Key for an Amazon S3 bucket.")
    bucket_file_name = fields.Char(string='Bucket Name',
                                   help="Field used to store the name of an"
                                        " Amazon S3 bucket.")
    aws_folder_name = fields.Char(string='File Name',
                                  help="field used to store the name of a"
                                       " folder in an Amazon S3 bucket.")
    success_message = fields.Char('Success Message', readonly=True)
    success_test = fields.Boolean(string="Success Test")
    fail_test = fields.Boolean(string="Fail Test")
    gdrive_backup_error_test = fields.Boolean(string="Google Drive Error Test")
    onedrive_backup_error_test = fields.Boolean(string="OneDrive Error Test")

    @api.depends('gdrive_access_token', 'gdrive_refresh_token')
    def _compute_is_google_drive_token_generated(self):
        """Set True if the Google Drive refresh token is generated"""
        for rec in self:
            rec.is_google_drive_token_generated = bool(
                rec.gdrive_access_token) and bool(rec.gdrive_refresh_token)

    @api.onchange('backup_destination')
    def _onchange_backup_destination(self):
        self.write({
            "fail_test": False,
            "success_test": False,
            "gdrive_backup_error_test": False,
            "onedrive_backup_error_test": False
        })

    @api.onchange('gdrive_client_key', 'gdrive_client_secret',
                  'google_drive_folder', 'onedrive_client_key',
                  'onedrive_client_secret', 'onedrive_folder_key', 'sftp_host',
                  'sftp_port', 'sftp_user', 'sftp_password', 'sftp_path',
                  'ftp_host', 'ftp_port', 'ftp_user', 'ft_password', 'ftp_path')
    def _onchange_gdrive_backup_error_test(self):
        if self.backup_destination == 'ftp':
            self.write({"success_test": False, "fail_test": True})
        if self.backup_destination == 'sftp':
            self.write({"success_test": False, "fail_test": True})
        if self.backup_destination == 'google_drive':
            if self.gdrive_backup_error_test:
                self.write({
                    "gdrive_backup_error_test": False
                })
        if self.backup_destination == 'onedrive':
            if self.onedrive_backup_error_test:
                self.write({
                    "onedrive_backup_error_test": False
                })

    def action_s3cloud(self):
        """If it has aws_secret_access_key, which will perform s3_cloud
         operations for connection test"""
        if self.aws_access_key and self.aws_secret_access_key:
            try:
                bo3 = boto3.client(
                    's3',
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_access_key)
                response = bo3.list_buckets()
                for bucket in response['Buckets']:
                    if self.bucket_file_name == bucket['Name']:
                        self.active = True
                        self.hide_active = True
                        self.write({"success_test": True, "fail_test": False})
                        return
                raise UserError(
                    _("Bucket not found. Please check the bucket name and"
                      " try again."))
            except Exception:
                self.write({"fail_test": True, "success_test": False})
                self.active = False
                self.hide_active = False

    def action_nextcloud(self):
        """If it has next_cloud_password, domain, and next_cloud_user_name
         which will perform an action for nextcloud connection test"""
        if self.domain and self.next_cloud_password and \
                self.next_cloud_user_name:
            try:
                ncx = NextCloud(self.domain,
                                auth=HTTPBasicAuth(self.next_cloud_user_name,
                                                   self.next_cloud_password))

                data = ncx.list_folders('/').__dict__
                if data['raw'].status_code == 207:
                    self.active = True
                    self.hide_active = True
                    self.write({"fail_test": False, "success_test": True})
                    return
                else:
                    self.active = False
                    self.hide_active = False
                    self.write({"fail_test": True, "success_test": False})
            except Exception:
                self.active = False
                self.hide_active = False
                self.write({"fail_test": True, "success_test": False})

    def _compute_redirect_uri(self):
        """Compute the redirect URI for onedrive and Google Drive"""
        for rec in self:
            base_url = request.env['ir.config_parameter'].get_param(
                'web.base.url')
            rec.onedrive_redirect_uri = base_url + '/onedrive/authentication'
            rec.gdrive_redirect_uri = base_url + '/google_drive/authentication'

    @api.depends('onedrive_access_token', 'onedrive_refresh_token')
    def _compute_is_onedrive_token_generated(self):
        """Set true if onedrive tokens are generated"""
        for rec in self:
            rec.is_onedrive_token_generated = bool(
                rec.onedrive_access_token) and bool(rec.onedrive_refresh_token)

    @api.depends('dropbox_refresh_token')
    def _compute_is_dropbox_token_generated(self):
        """Set True if the dropbox refresh token is generated"""
        for rec in self:
            rec.is_dropbox_token_generated = bool(rec.dropbox_refresh_token)

    def action_get_dropbox_auth_code(self):
        """Open a wizards to set up dropbox Authorization code"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dropbox Authorization Wizard',
            'res_model': 'dropbox.auth.code',
            'view_mode': 'form',
            'target': 'new',
            'context': {'dropbox_auth': True}
        }

    def action_get_onedrive_auth_code(self):
        """Generate onedrive authorization code"""
        AUTHORITY = \
            'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
        action = self.env.ref(
            "auto_database_backup.action_db_backup_configure")
        action_data = {
            'id': action.id,
            'name': action.name,
            'type': action.type,
            'xml_id': action.xml_id,
            'help': action.help,
            'binding_model_id': action.binding_model_id,
            'binding_type': action.binding_type,
            'display_name': action.display_name,
            'res_model': action.res_model,
            'target': action.target,
            'view_mode': action.view_mode,
            'views': action.views,
            'groups_id': [(6, 0, action.groups_id.ids)],
            'search_view_id': action.search_view_id.id if action.search_view_id else False,
            'filter': action.filter,
            'search_view': action.search_view,
            'limit': action.limit,
        }
        base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        url_return = base_url + \
                     '/web#id=%d&action=%d&view_type=form&model=%s' % (
                         self.id, action_data['id'], 'db.backup.configure')
        state = {
            'backup_config_id': self.id,
            'url_return': url_return
        }
        encoded_params = urls.url_encode({
            'response_type': 'code',
            'client_id': self.onedrive_client_key,
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
        """Generate google drive authorization code"""
        action = self.env.ref(
            "auto_database_backup.action_db_backup_configure")
        action_data = {
            'id': action.id,
            'name': action.name,
            'type': action.type,
            'xml_id': action.xml_id,
            'help': action.help,
            'binding_model_id': action.binding_model_id,
            'binding_type': action.binding_type,
            'display_name': action.display_name,
            'res_model': action.res_model,
            'target': action.target,
            'view_mode': action.view_mode,
            'views': action.views,
            'groups_id': [(6, 0, action.groups_id.ids)],
            'search_view_id': action.search_view_id.id if action.search_view_id else False,
            'filter': action.filter,
            'search_view': action.search_view,
            'limit': action.limit,
        }
        base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        url_return = base_url + \
                     '/web#id=%d&action=%d&view_type=form&model=%s' % (
                         self.id, action_data['id'], 'db.backup.configure')
        state = {
            'backup_config_id': self.id,
            'url_return': url_return
        }
        encoded_params = urls.url_encode({
            'response_type': 'code',
            'client_id': self.gdrive_client_key,
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

    def get_gdrive_tokens(self, authorize_code):
        """Generate onedrive tokens from authorization code."""
        base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            'code': authorize_code,
            'client_id': self.gdrive_client_key,
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
                if self.gdrive_backup_error_test:
                    self.write({
                        'gdrive_backup_error_test': False
                    })
        except Exception:
            if not self.gdrive_backup_error_test:
                self.write({"gdrive_backup_error_test": True})

    def generate_onedrive_refresh_token(self):
        """Generate onedrive access token from refresh token if expired"""
        base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        data = {
            'client_id': self.onedrive_client_key,
            'client_secret': self.onedrive_client_secret,
            'scope': ONEDRIVE_SCOPE,
            'grant_type': "refresh_token",
            'redirect_uri': base_url + '/onedrive/authentication',
            'refresh_token': self.onedrive_refresh_token
        }
        try:
            res = requests.post(
                "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                data=data, headers=headers)
            res.raise_for_status()
            response = res.content and res.json() or {}
            if response:
                expires_in = response.get('expires_in')
                self.write({
                    'onedrive_access_token': response.get('access_token'),
                    'onedrive_refresh_token': response.get('refresh_token'),
                    'onedrive_token_validity': fields.Datetime.now() + timedelta(
                        seconds=expires_in) if expires_in else False,
                })
        except requests.HTTPError as error:
            _logger.exception("Bad microsoft onedrive request : %s !",
                              error.response.content)
            raise error

    def get_onedrive_tokens(self, authorize_code):
        """Generate onedrive tokens from authorization code."""
        headers = {"content-type": "application/x-www-form-urlencoded"}
        base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        data = {
            'code': authorize_code,
            'client_id': self.onedrive_client_key,
            'client_secret': self.onedrive_client_secret,
            'grant_type': 'authorization_code',
            'scope': ONEDRIVE_SCOPE,
            'redirect_uri': base_url + '/onedrive/authentication'
        }
        try:
            res = requests.post(
                "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                data=data, headers=headers)
            res.raise_for_status()
            response = res.content and res.json() or {}
            if response:
                expires_in = response.get('expires_in')
                self.write({
                    'onedrive_access_token': response.get('access_token'),
                    'onedrive_refresh_token': response.get('refresh_token'),
                    'onedrive_token_validity': fields.Datetime.now() + timedelta(
                        seconds=expires_in) if expires_in else False,
                })
                if self.onedrive_backup_error_test:
                    self.write({
                        'onedrive_backup_error_test': False
                    })
        except Exception:
            if not self.onedrive_backup_error_test:
                self.write({"onedrive_backup_error_test": True})

    def generate_gdrive_refresh_token(self):
        """Generate Google Drive access token from refresh token if expired"""
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            'refresh_token': self.gdrive_refresh_token,
            'client_id': self.gdrive_client_key,
            'client_secret': self.gdrive_client_secret,
            'grant_type': 'refresh_token',
        }
        try:
            res = requests.post(GOOGLE_TOKEN_ENDPOINT, data=data,
                                headers=headers)
            res.raise_for_status()
            response = res.content and res.json() or {}
            if response:
                expires_in = response.get('expires_in')
                self.write({
                    'gdrive_access_token': response.get('access_token'),
                    'gdrive_token_validity': fields.Datetime.now() + timedelta(
                        seconds=expires_in) if expires_in else False,
                })
        except requests.HTTPError as error:
            error_key = error.response.json().get("error", "nc")
            error_msg = _(
                "An error occurred while generating the token. Your"
                "authorization code may be invalid or has already expired [%s]."
                "You should check your Client ID and secret on the Google APIs"
                " platform or try to stop and restart your calendar"
                " synchronisation.",
                error_key)
            raise UserError(error_msg)

    def get_dropbox_auth_url(self):
        """Return dropbox authorization url"""
        dbx_auth = dropbox.oauth.DropboxOAuth2FlowNoRedirect(
            self.dropbox_client_key,
            self.dropbox_client_secret,
            token_access_type='offline')
        return dbx_auth.start()

    def set_dropbox_refresh_token(self, auth_code):
        """Generate and set the dropbox refresh token from authorization code"""
        try:
            dbx_auth = dropbox.oauth.DropboxOAuth2FlowNoRedirect(
                self.dropbox_client_key,
                self.dropbox_client_secret,
                token_access_type='offline')
            outh_result = dbx_auth.finish(auth_code)
            self.dropbox_refresh_token = outh_result.refresh_token
        except Exception:
            raise ValidationError(
                'Please Enter Valid Authentication Code')

    @api.constrains('db_name', 'master_pwd')
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
        """Test the sftp and ftp connection using entered credentials"""
        if self.backup_destination == 'sftp':
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(hostname=self.sftp_host,
                               username=self.sftp_user,
                               password=self.sftp_password,
                               port=self.sftp_port)
                sftp = client.open_sftp()
                sftp.close()
            except Exception:
                raise UserError(
                    _("It seems there was an issue with the connection, "
                      "possibly due to incorrect information provided. "
                      "Please double-check all the information you provided "
                      "for the connection to ensure it is correct."))
            finally:
                client.close()
        elif self.backup_destination == 'ftp':
            try:
                ftp_server = ftplib.FTP()
                ftp_server.connect(self.ftp_host, int(self.ftp_port))
                ftp_server.login(self.ftp_user, self.ftp_password)
                ftp_server.quit()
            except Exception:
                raise UserError(
                    _("It seems there was an issue with the connection, "
                      "possibly due to incorrect information provided. "
                      "Please double-check all the information you provided "
                      "for the connection to ensure it is correct."))
        self.write({"success_test": True})

    def _schedule_auto_backup(self):
        """Function for generating and storing backup
        Database backup for all the active records in backup configuration
        model will be created"""
        records = self.search([])
        mail_template_success = self.env.ref(
            'auto_database_backup.mail_template_data_db_backup_successful')
        mail_template_failed = self.env.ref(
            'auto_database_backup.mail_template_data_db_backup_failed')
        for rec in records:
            backup_time = datetime.datetime.utcnow().strftime(
                "%Y-%m-%d_%H-%M-%S")
            backup_filename = "%s_%s.%s" % (
                rec.db_name, backup_time, rec.backup_format)
            rec.backup_filename = backup_filename
            # Local backup
            if rec.backup_destination == 'local':
                try:
                    if not os.path.isdir(rec.backup_path):
                        os.makedirs(rec.backup_path)
                    backup_file = os.path.join(rec.backup_path,
                                               backup_filename)
                    file_open = open(backup_file, "wb")
                    odoo.service.db.dump_db(rec.db_name, file_open,
                                            rec.backup_format)
                    file_open.close()
                    # remove older backups
                    if rec.auto_remove:
                        for filename in os.listdir(rec.backup_path):
                            file = os.path.join(rec.backup_path, filename)
                            create_time = datetime.datetime.fromtimestamp(
                                os.path.getctime(file))
                            backup_duration = \
                                datetime.datetime.utcnow() - create_time
                            if backup_duration.days >= rec.days_to_remove:
                                os.remove(file)
                    if rec.notify_user:
                        mail_template_success.send_mail(rec.id,
                                                        force_send=True)
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
                    temp = tempfile.NamedTemporaryFile(
                        suffix='.%s' % rec.backup_format)
                    try:
                        ftp_server.cwd(rec.ftp_path)
                    except ftplib.error_perm:
                        ftp_server.mkd(rec.ftp_path)
                        ftp_server.cwd(rec.ftp_path)
                    with open(temp.name, "wb+") as tmp:
                        odoo.service.db.dump_db(rec.db_name, tmp,
                                                rec.backup_format)
                    ftp_server.storbinary('STOR %s' % backup_filename,
                                          open(temp.name, "rb"))
                    if rec.auto_remove:
                        files = ftp_server.nlst()
                        for file_open in files:
                            create_time = datetime.datetime.strptime(
                                ftp_server.
                                sendcmd(
                                    'MDTM ' + file_open)[4:], "%Y%m%d%H%M%S")
                            diff_days = (
                                    datetime.datetime.now() -
                                    create_time).days
                            if diff_days >= rec.days_to_remove:
                                ftp_server.delete(file_open)
                    ftp_server.quit()
                    if rec.notify_user:
                        mail_template_success.send_mail(rec.id,
                                                        force_send=True)
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
                    client.connect(hostname=rec.sftp_host,
                                   username=rec.sftp_user,
                                   password=rec.sftp_password,
                                   port=rec.sftp_port)
                    sftp = client.open_sftp()
                    temp = tempfile.NamedTemporaryFile(
                        suffix='.%s' % rec.backup_format)
                    with open(temp.name, "wb+") as tmp:
                        odoo.service.db.dump_db(rec.db_name, tmp,
                                                rec.backup_format)
                    try:
                        sftp.chdir(rec.sftp_path)
                    except IOError as e:
                        if e.errno == errno.ENOENT:
                            sftp.mkdir(rec.sftp_path)
                            sftp.chdir(rec.sftp_path)
                    sftp.put(temp.name, backup_filename)
                    if rec.auto_remove:
                        files = sftp.listdir()
                        expired = list(filter(lambda fl:
                                              (datetime.datetime.now() -
                                               datetime.datetime.fromtimestamp(
                                                   sftp.stat(fl).
                                                   st_mtime)).
                                              days >= rec.days_to_remove,
                                              files))
                        for file in expired:
                            sftp.unlink(file)
                    sftp.close()
                    if rec.notify_user:
                        mail_template_success.send_mail(rec.id,
                                                        force_send=True)
                except Exception as e:
                    rec.generated_exception = e
                    _logger.info('SFTP Exception: %s', e)
                    if rec.notify_user:
                        mail_template_failed.send_mail(rec.id, force_send=True)
                finally:
                    client.close()
            # Google Drive backup
            elif rec.backup_destination == 'google_drive':
                try:
                    if rec.gdrive_token_validity <= fields.Datetime.now():
                        rec.generate_gdrive_refresh_token()
                    temp = tempfile.NamedTemporaryFile(
                        suffix='.%s' % rec.backup_format)
                    with open(temp.name, "wb+") as tmp:
                        odoo.service.db.dump_db(rec.db_name, tmp,
                                                rec.backup_format)
                    try:
                        headers = {
                            "Authorization": "Bearer %s" % rec.gdrive_access_token}
                        para = {
                            "name": backup_filename,
                            "parents": [rec.google_drive_folder],
                        }
                        files = {
                            'data': ('metadata', json.dumps(para),
                                     'application/json; charset=UTF-8'),
                            'file': open(temp.name, "rb")
                        }
                        requests.post(
                            "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
                            headers=headers,
                            files=files
                        )
                        if rec.auto_remove:
                            query = "parents = '%s'" % rec.google_drive_folder_key
                            files_req = requests.get(
                                "https://www.googleapis.com/drive/v3/files?q=%s" % query,
                                headers=headers)
                            files = files_req.json()['files']
                            for file in files:
                                file_date_req = requests.get(
                                    "https://www.googleapis.com/drive/v3/files/%s?fields=createdTime" %
                                    file['id'], headers=headers)
                                create_time = file_date_req.json()[
                                                  'createdTime'][
                                              :19].replace('T', ' ')
                                diff_days = (
                                        fields.datetime.now() - fields.datetime.strptime(
                                    create_time, '%Y-%m-%d %H:%M:%S')).days
                                if diff_days >= rec.days_to_remove:
                                    requests.delete(
                                        "https://www.googleapis.com/drive/v3/files/%s" %
                                        file['id'], headers=headers)
                        if rec.notify_user:
                            mail_template_success.send_mail(rec.id,
                                                            force_send=True)
                    except Exception as e:
                        rec.generated_exception = e
                        _logger.info('Google Drive Exception: %s', e)
                        if rec.notify_user:
                            mail_template_failed.send_mail(rec.id,
                                                           force_send=True)
                except Exception:
                    if rec.notify_user:
                        mail_template_failed.send_mail(rec.id,
                                                       force_send=True)
                        raise ValidationError(
                            'Please check the credentials before activation')
                    else:
                        raise ValidationError('Please check connection')
            # Dropbox backup
            elif rec.backup_destination == 'dropbox':
                try:
                    temp = tempfile.NamedTemporaryFile(
                        suffix='.%s' % rec.backup_format)
                    with open(temp.name, "wb+") as tmp:
                        odoo.service.db.dump_db(rec.db_name, tmp,
                                                rec.backup_format)
                    try:
                        dbx = dropbox.Dropbox(
                            app_key=rec.dropbox_client_key,
                            app_secret=rec.dropbox_client_secret,
                            oauth2_refresh_token=rec.dropbox_refresh_token)
                        dropbox_destination = (rec.dropbox_folder + '/' +
                                               backup_filename)
                        dbx.files_upload(temp.read(), dropbox_destination)
                        if rec.auto_remove:
                            files = dbx.files_list_folder(
                                rec.dropbox_folder)
                            file_entries = files.entries
                            expired_files = list(filter(
                                lambda fl: (fields.datetime.now() -
                                            fl.client_modified).days >=
                                           rec.days_to_remove,
                                file_entries))
                            for file in expired_files:
                                dbx.files_delete_v2(file.path_display)
                        if rec.notify_user:
                            mail_template_success.send_mail(rec.id,
                                                            force_send=True)
                    except Exception as error:
                        rec.generated_exception = error
                        _logger.info('Dropbox Exception: %s', error)
                        if rec.notify_user:
                            mail_template_failed.send_mail(rec.id,
                                                           force_send=True)
                except Exception:
                    if rec.notify_user:
                        mail_template_failed.send_mail(rec.id, force_send=True)
                        raise ValidationError(
                            'Please check the credentials before activation')
                    else:
                        raise ValidationError('Please check connection')
            # Onedrive Backup
            elif rec.backup_destination == 'onedrive':
                try:
                    if rec.onedrive_token_validity <= fields.Datetime.now():
                        rec.generate_onedrive_refresh_token()
                    temp = tempfile.NamedTemporaryFile(
                        suffix='.%s' % rec.backup_format)
                    with open(temp.name, "wb+") as tmp:
                        odoo.service.db.dump_db(rec.db_name, tmp,
                                                rec.backup_format)
                    headers = {
                        'Authorization': 'Bearer %s' % rec.onedrive_access_token,
                        'Content-Type': 'application/json'}
                    upload_session_url = MICROSOFT_GRAPH_END_POINT + "/v1.0/me/drive/items/%s:/%s:/createUploadSession" % (
                        rec.onedrive_folder_key, backup_filename)
                    try:
                        upload_session = requests.post(upload_session_url,
                                                       headers=headers)
                        upload_url = upload_session.json().get('uploadUrl')
                        requests.put(upload_url, data=temp.read())
                        if rec.auto_remove:
                            list_url = MICROSOFT_GRAPH_END_POINT + "/v1.0/me/drive/items/%s/children" % rec.onedrive_folder_key
                            response = requests.get(list_url, headers=headers)
                            files = response.json().get('value')
                            for file in files:
                                create_time = file['createdDateTime'][
                                              :19].replace(
                                    'T',
                                    ' ')
                                diff_days = (
                                        fields.datetime.now() - fields.datetime.strptime(
                                    create_time, '%Y-%m-%d %H:%M:%S')).days
                                if diff_days >= rec.days_to_remove:
                                    delete_url = MICROSOFT_GRAPH_END_POINT + "/v1.0/me/drive/items/%s" % \
                                                 file['id']
                                    requests.delete(delete_url, headers=headers)
                        if rec.notify_user:
                            mail_template_success.send_mail(rec.id,
                                                            force_send=True)
                    except Exception as error:
                        rec.generated_exception = error
                        _logger.info('Onedrive Exception: %s', error)
                        if rec.notify_user:
                            mail_template_failed.send_mail(rec.id,
                                                           force_send=True)
                except Exception:
                    if rec.notify_user:
                        mail_template_failed.send_mail(rec.id, force_send=True)
                        raise ValidationError(
                            'Please check the credentials before activation')
                    else:
                        raise ValidationError('Please check connection')
            # NextCloud Backup
            elif rec.backup_destination == 'next_cloud':
                try:
                    if rec.domain and rec.next_cloud_password and \
                            rec.next_cloud_user_name:
                        try:
                            # Connect to NextCloud using the provided username
                            # and password
                            ncx = NextCloud(rec.domain,
                                            auth=HTTPBasicAuth(
                                                rec.next_cloud_user_name,
                                                rec.next_cloud_password))
                            # Connect to NextCloud again to perform additional
                            # operations
                            nc = nextcloud_client.Client(rec.domain)
                            nc.login(rec.next_cloud_user_name,
                                     rec.next_cloud_password)
                            # Get the folder name from the NextCloud folder ID
                            folder_name = rec.nextcloud_folder_key
                            # If auto_remove is enabled, remove backup files
                            # older than specified days
                            if rec.auto_remove:
                                folder_path = "/" + folder_name
                                for item in nc.list(folder_path):
                                    backup_file_name = item.path.split("/")[-1]
                                    backup_date_str = \
                                        backup_file_name.split("_")[
                                            2]
                                    backup_date = fields.datetime.strptime(
                                        backup_date_str, '%Y-%m-%d').date()
                                    if (fields.date.today() - backup_date).days \
                                            >= rec.days_to_remove:
                                        nc.delete(item.path)
                            # If notify_user is enabled, send a success email
                            # notification
                            if rec.notify_user:
                                mail_template_success.send_mail(rec.id,
                                                                force_send=True)
                        except Exception as error:
                            rec.generated_exception = error
                            _logger.info('NextCloud Exception: %s', error)
                            if rec.notify_user:
                                # If an exception occurs, send a failed email
                                # notification
                                mail_template_failed.send_mail(rec.id,
                                                               force_send=True)
                        # Get the list of folders in the root directory of NextCloud
                        data = ncx.list_folders('/').__dict__
                        folders = [
                            [file_name['href'].split('/')[-2],
                             file_name['file_id']]
                            for file_name in data['data'] if
                            file_name['href'].endswith('/')]
                        # If the folder name is not found in the list of folders,
                        # create the folder
                        if folder_name not in [file[0] for file in folders]:
                            nc.mkdir(folder_name)
                            # Dump the database to a temporary file
                            temp = tempfile.NamedTemporaryFile(
                                suffix='.%s' % rec.backup_format)
                            with open(temp.name, "wb+") as tmp:
                                odoo.service.db.dump_db(rec.db_name, tmp,
                                                        rec.backup_format)
                            backup_file_path = temp.name
                            remote_file_path = f"/{folder_name}/{rec.db_name}_" \
                                               f"{backup_time}.{rec.backup_format}"
                            nc.put_file(remote_file_path, backup_file_path)
                        else:
                            # Dump the database to a temporary file
                            temp = tempfile.NamedTemporaryFile(
                                suffix='.%s' % rec.backup_format)
                            with open(temp.name, "wb+") as tmp:
                                odoo.service.db.dump_db(rec.db_name, tmp,
                                                        rec.backup_format)
                            backup_file_path = temp.name
                            remote_file_path = f"/{folder_name}/{rec.db_name}_" \
                                               f"{backup_time}.{rec.backup_format}"
                            nc.put_file(remote_file_path, backup_file_path)
                except Exception:
                    raise ValidationError('Please check connection')
            # Amazon S3 Backup
            elif rec.backup_destination == 'amazon_s3':
                if rec.aws_access_key and rec.aws_secret_access_key:
                    try:
                        # Create a boto3 client for Amazon S3 with provided
                        # access key id and secret access key
                        bo3 = boto3.client(
                            's3',
                            aws_access_key_id=rec.aws_access_key,
                            aws_secret_access_key=rec.aws_secret_access_key)
                        # If auto_remove is enabled, remove the backups that
                        # are older than specified days from the S3 bucket
                        if rec.auto_remove:
                            folder_path = rec.aws_folder_name
                            response = bo3.list_objects(
                                Bucket=rec.bucket_file_name,
                                Prefix=folder_path)
                            today = fields.date.today()
                            for file in response['Contents']:
                                file_path = file['Key']
                                last_modified = file['LastModified']
                                date = last_modified.date()
                                age_in_days = (today - date).days
                                if age_in_days >= rec.days_to_remove:
                                    bo3.delete_object(
                                        Bucket=rec.bucket_file_name,
                                        Key=file_path)
                        # Create a boto3 resource for Amazon S3 with provided
                        # access key id and secret access key
                        s3 = boto3.resource(
                            's3',
                            aws_access_key_id=rec.aws_access_key,
                            aws_secret_access_key=rec.aws_secret_access_key)
                        # Create a folder in the specified bucket, if it
                        # doesn't already exist
                        s3.Object(rec.bucket_file_name,
                                  rec.aws_folder_name + '/').put()
                        bucket = s3.Bucket(rec.bucket_file_name)
                        # Get all the prefixes in the bucket
                        prefixes = set()
                        for obj in bucket.objects.all():
                            key = obj.key
                            if key.endswith('/'):
                                prefix = key[:-1]  # Remove the trailing slash
                                prefixes.add(prefix)
                        # If the specified folder is present in the bucket,
                        # take a backup of the database and upload it to the
                        #   S3 bucket
                        if rec.aws_folder_name in prefixes:
                            temp = tempfile.NamedTemporaryFile(
                                suffix='.%s' % rec.backup_format)
                            with open(temp.name, "wb+") as tmp:
                                odoo.service.db.dump_db(rec.db_name, tmp,
                                                        rec.backup_format)
                            backup_file_path = temp.name
                            remote_file_path = f"{rec.aws_folder_name}/{rec.db_name}_" \
                                               f"{backup_time}.{rec.backup_format}"
                            s3.Object(rec.bucket_file_name,
                                      remote_file_path).upload_file(
                                backup_file_path)
                            # If notify_user is enabled, send email to the
                            # user notifying them about the successful backup
                            if rec.notify_user:
                                mail_template_success.send_mail(rec.id,
                                                                force_send=True)
                    except Exception as error:
                        # If any error occurs, set the 'generated_exception'
                        # field to the error message and log the error
                        rec.generated_exception = error
                        _logger.info('Amazon S3 Exception: %s', error)
                        # If notify_user is enabled, send email to the user
                        # notifying them about the failed backup
                        if rec.notify_user:
                            mail_template_failed.send_mail(rec.id,
                                                           force_send=True)
