# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aslam AK (odoo@cybrosys.com)
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
###############################################################################
import ftplib
import gdown
import odoo
import odoo.modules.registry
import os
import paramiko
import requests
import tempfile
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.http import dispatch_rpc
from odoo.service import db
from odoo.tools.misc import str2bool


class DataBaseRestore(models.TransientModel):
    """
    Database Restore Model
    """
    _name = "database.restore"
    _description = "Restore Backups"

    db_file = fields.Char(string="File",
                          help="Path or URL to the database backup file")
    db_name = fields.Char(string="Database Name",
                          help="Name of the database to restore")
    db_master_pwd = fields.Char(string="Database Master Password",
                                help="Master password for the database")
    backup_location = fields.Char(string="Backup Location",
                                  help="Location where the database backup is "
                                       "stored")

    def action_restore_database(self, copy=False):
        """
        Function to restore the database Backups
        """
        insecure = odoo.tools.config.verify_admin_password('admin')
        if insecure and self.db_master_pwd:
            dispatch_rpc('db', 'change_admin_password',
                         ["admin", self.db_master_pwd])
        try:
            db.check_super(self.db_master_pwd)
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            if self.backup_location == 'Google Drive':
                gdown.download(self.db_file, temp_file.name, quiet=False)
            elif self.backup_location in ['Dropbox', 'OneDrive']:
                response = requests.get(self.db_file, stream=True)
                temp_file.write(response.content)
            elif self.backup_location == 'FTP Storage':
                for rec in self.env['db.backup.configure'].search([]):
                    if rec.backup_destination == 'ftp' and \
                            rec.ftp_path == os.path.dirname(self.db_file):
                        ftp_server = ftplib.FTP()
                        ftp_server.connect(rec.ftp_host, int(rec.ftp_port))
                        ftp_server.login(rec.ftp_user, rec.ftp_password)
                        ftp_server.retrbinary("RETR " + self.db_file,
                                              temp_file.write)
                        temp_file.seek(0)
                        ftp_server.quit()
            elif self.backup_location == 'SFTP Storage':
                for rec in self.env['db.backup.configure'].search([]):
                    if rec.backup_destination == 'sftp' and \
                            rec.sftp_path == os.path.dirname(self.db_file):
                        sftp_client = paramiko.SSHClient()
                        sftp_client.set_missing_host_key_policy(
                            paramiko.AutoAddPolicy())
                        sftp_client.connect(hostname=rec.sftp_host,
                                            username=rec.sftp_user,
                                            password=rec.sftp_password,
                                            port=rec.sftp_port)
                        sftp_server = sftp_client.open_sftp()
                        sftp_server.getfo(self.db_file, temp_file)
                        sftp_server.close()
                        sftp_client.close()
            elif self.backup_location == 'Local Storage':
                temp_file.name = self.db_file
            db.restore_db(self.db_name, temp_file.name, str2bool(copy))
            temp_file.close()
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/database/manager'
            }
        except Exception as error:
            raise UserError(
                _("Database restore error: %s" % (str(error) or repr(error))))
