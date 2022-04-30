# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
        ('sftp', 'SFTP')
    ], string='Backup Destination')
    backup_path = fields.Char(string='Backup Path', help='Local storage directory path')
    sftp_host = fields.Char(string='SFTP Host')
    sftp_port = fields.Char(string='SFTP Port', default=22)
    sftp_user = fields.Char(string='SFTP User')
    sftp_password = fields.Char(string='SFTP Password')
    sftp_path = fields.Char(string='SFTP Path')
    ftp_host = fields.Char(string='FTP Host')
    ftp_port = fields.Char(string='FTP Port', default=21)
    ftp_user = fields.Char(string='FTP User')
    ftp_password = fields.Char(string='FTP Password')
    ftp_path = fields.Char(string='FTP Path')
    active = fields.Boolean(default=True)
    save_to_drive = fields.Boolean()
    auto_remove = fields.Boolean(string='Remove Old Backups')
    days_to_remove = fields.Integer(string='Remove After',
                                    help='Automatically delete stored backups after this specified number of days')
    google_drive_folderid = fields.Char(string='Drive Folder ID')
    notify_user = fields.Boolean(string='Notify User',
                                 help='Send an email notification to user when the backup operation is successful or failed')
    user_id = fields.Many2one('res.users', string='User')
    backup_filename = fields.Char(string='Backup Filename', help='For Storing generated backup filename')
    generated_exception = fields.Char(string='Exception', help='Exception Encountered while Backup generation')

    @api.constrains('db_name', 'master_pwd')
    def _check_db_credentials(self):
        """
        Validate enetered database name and master password
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
                temp = tempfile.NamedTemporaryFile(suffix='.%s' % rec.backup_format)
                with open(temp.name, "wb+") as tmp:
                    odoo.service.db.dump_db(rec.db_name, tmp, rec.backup_format)
                try:
                    access_token = self.env['google.drive.config'].sudo().get_access_token()
                    headers = {"Authorization": "Bearer %s" % access_token}
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
