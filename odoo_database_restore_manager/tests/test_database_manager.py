# -*- coding: utf-8 -*-
###############################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#   You can modify it under the terms of the GNU AFFERO
#   GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#   You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#   (AGPL v3) along with this program.
#   If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
import tempfile
from datetime import timedelta
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.tests.common import TransactionCase


class TestDatabaseManager(TransactionCase):
    """Test suite for database.manager model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.DatabaseManager = cls.env['database.manager']
        cls.BackupConfigure = cls.env['db.backup.configure']
        cls.company_id = cls.env.company.id

    def setUp(self):
        super().setUp()
        # Patch credential check constraint on auto_database_backup so record creation succeeds in tests
        self.check_cred_patcher = patch(
            'odoo.addons.auto_database_backup.models.db_backup_configure.DbBackupConfigure._check_db_credentials',
            return_value=True
        )
        self.check_cred_patcher.start()
        self.addCleanup(self.check_cred_patcher.stop)

        # Clean up any existing backup configurations to ensure isolated test runs
        self.BackupConfigure.with_context(active_test=False).search([]).unlink()

    def _get_mock_request(self):
        """Helper to create mock HTTP request with company cookies."""
        mock_req = MagicMock()
        mock_req.httprequest.cookies.get.return_value = [self.company_id]
        return mock_req

    def test_action_import_files_no_backup_count(self):
        """Test action_import_files when backup_count is 0 or negative."""
        self.env['ir.config_parameter'].set_param(
            'odoo_database_restore_manager.backup_count', '0'
        )
        with patch('odoo.addons.odoo_database_restore_manager.models.database_manager.request', self._get_mock_request()):
            res = self.DatabaseManager.action_import_files()
            self.assertEqual(res[0], 'error')
            self.assertEqual(res[1], 'Please set a backup count')
            self.assertEqual(res[2], 'Storages')
            self.assertEqual(res[3], self.company_id)

    def test_action_import_files_no_backups_configured(self):
        """Test action_import_files when backup count is set but no backup configs exist."""
        self.env['ir.config_parameter'].set_param(
            'odoo_database_restore_manager.backup_count', '5'
        )
        with patch('odoo.addons.odoo_database_restore_manager.models.database_manager.request', self._get_mock_request()):
            res = self.DatabaseManager.action_import_files()
            self.assertEqual(res[0], 'error')
            self.assertEqual(res[1], 'No Backups Found')
            self.assertEqual(res[2], 'auto_database_backup')
            self.assertEqual(res[3], self.company_id)

    def test_action_import_files_local_destination(self):
        """Test action_import_files with local storage backup destination."""
        self.env['ir.config_parameter'].set_param(
            'odoo_database_restore_manager.backup_count', '5'
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, 'test_backup.zip')
            with open(test_file, 'w') as f:
                f.write('dummy backup content')

            self.BackupConfigure.create({
                'name': 'Local Config',
                'db_name': self.env.cr.dbname,
                'master_pwd': 'admin',
                'backup_destination': 'local',
                'backup_path': temp_dir,
                'active': True,
            })

            with patch('odoo.addons.odoo_database_restore_manager.models.database_manager.request', self._get_mock_request()):
                res = self.DatabaseManager.action_import_files()
                self.assertIsInstance(res, list)
                self.assertIsInstance(res[0], dict)
                self.assertIn('test_backup.zip', res[0])
                self.assertEqual(res[0]['test_backup.zip'][1], 'Local Storage')
                self.assertEqual(res[1], self.company_id)

    def test_action_import_files_local_exception(self):
        """Test action_import_files when local storage retrieval raises an exception."""
        self.env['ir.config_parameter'].set_param(
            'odoo_database_restore_manager.backup_count', '5'
        )
        self.BackupConfigure.create({
            'name': 'Invalid Local Config',
            'db_name': self.env.cr.dbname,
            'master_pwd': 'admin',
            'backup_destination': 'local',
            'backup_path': '/path_that_does_not_exist_xyz123',
            'active': True,
        })

        with patch('odoo.addons.odoo_database_restore_manager.models.database_manager.request', self._get_mock_request()):
            with patch('os.walk', side_effect=Exception('Local read error')):
                res = self.DatabaseManager.action_import_files()
                self.assertEqual(res[0], 'error')
                self.assertEqual(res[2], 'Local')

    def test_action_import_files_dropbox_destination(self):
        """Test action_import_files with Dropbox backup destination."""
        self.env['ir.config_parameter'].set_param(
            'odoo_database_restore_manager.backup_count', '5'
        )
        self.BackupConfigure.create({
            'name': 'Dropbox Config',
            'db_name': self.env.cr.dbname,
            'master_pwd': 'admin',
            'backup_destination': 'dropbox',
            'dropbox_client_key': 'key',
            'dropbox_client_secret': 'secret',
            'dropbox_refresh_token': 'token',
            'dropbox_folder': '/backups',
            'active': True,
        })

        mock_entry = MagicMock()
        mock_entry.path_lower = '/backups/db_backup.zip'
        mock_entry.client_modified = fields.Datetime.now()

        mock_temporary_link = MagicMock()
        mock_temporary_link.metadata.name = 'db_backup.zip'
        mock_temporary_link.link = 'https://dropbox.com/download/db_backup.zip'

        mock_dbx = MagicMock()
        mock_dbx.files_list_folder.return_value.entries = [mock_entry]
        mock_dbx.files_get_temporary_link.return_value = mock_temporary_link

        with patch('odoo.addons.odoo_database_restore_manager.models.database_manager.request', self._get_mock_request()):
            with patch('dropbox.Dropbox', return_value=mock_dbx):
                res = self.DatabaseManager.action_import_files()
                self.assertIsInstance(res[0], dict)
                self.assertIn('db_backup.zip', res[0])
                self.assertEqual(res[0]['db_backup.zip'][1], 'Dropbox')

    def test_action_import_files_dropbox_exception(self):
        """Test action_import_files when Dropbox retrieval fails."""
        self.env['ir.config_parameter'].set_param(
            'odoo_database_restore_manager.backup_count', '5'
        )
        self.BackupConfigure.create({
            'name': 'Dropbox Config',
            'db_name': self.env.cr.dbname,
            'master_pwd': 'admin',
            'backup_destination': 'dropbox',
            'dropbox_client_key': 'key',
            'dropbox_client_secret': 'secret',
            'dropbox_refresh_token': 'token',
            'dropbox_folder': '/backups',
            'active': True,
        })

        with patch('odoo.addons.odoo_database_restore_manager.models.database_manager.request', self._get_mock_request()):
            with patch('dropbox.Dropbox', side_effect=Exception('Dropbox Auth Error')):
                res = self.DatabaseManager.action_import_files()
                self.assertEqual(res[0], 'error')
                self.assertEqual(res[2], 'Dropbox')

    def test_action_import_files_onedrive_destination(self):
        """Test action_import_files with OneDrive backup destination."""
        self.env['ir.config_parameter'].set_param(
            'odoo_database_restore_manager.backup_count', '5'
        )
        self.BackupConfigure.create({
            'name': 'OneDrive Config',
            'db_name': self.env.cr.dbname,
            'master_pwd': 'admin',
            'backup_destination': 'onedrive',
            'onedrive_access_token': 'access_token',
            'onedrive_folder_key': 'folder_key',
            'onedrive_token_validity': fields.Datetime.now() + timedelta(days=1),
            'active': True,
        })

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'value': [{
                '@microsoft.graph.downloadUrl': 'https://onedrive.com/file',
                'name': 'onedrive_backup.zip',
                'createdDateTime': '2026-01-01T12:00:00Z',
            }]
        }

        with patch('odoo.addons.odoo_database_restore_manager.models.database_manager.request', self._get_mock_request()):
            with patch('requests.request', return_value=mock_response):
                res = self.DatabaseManager.action_import_files()
                self.assertIsInstance(res[0], dict)
                self.assertIn('onedrive_backup.zip', res[0])
                self.assertEqual(res[0]['onedrive_backup.zip'][1], 'OneDrive')

    def test_action_import_files_onedrive_exception(self):
        """Test action_import_files when OneDrive API raises an error."""
        self.env['ir.config_parameter'].set_param(
            'odoo_database_restore_manager.backup_count', '5'
        )
        self.BackupConfigure.create({
            'name': 'OneDrive Config',
            'db_name': self.env.cr.dbname,
            'master_pwd': 'admin',
            'backup_destination': 'onedrive',
            'onedrive_access_token': 'token',
            'onedrive_folder_key': 'folder',
            'onedrive_token_validity': fields.Datetime.now() + timedelta(days=1),
            'active': True,
        })

        with patch('odoo.addons.odoo_database_restore_manager.models.database_manager.request', self._get_mock_request()):
            with patch('requests.request', side_effect=Exception('OneDrive Error')):
                res = self.DatabaseManager.action_import_files()
                self.assertEqual(res[0], 'error')
                self.assertEqual(res[2], 'OneDrive')

    def test_action_import_files_google_drive_destination(self):
        """Test action_import_files with Google Drive backup destination."""
        self.env['ir.config_parameter'].set_param(
            'odoo_database_restore_manager.backup_count', '5'
        )
        self.BackupConfigure.create({
            'name': 'Google Drive Config',
            'db_name': self.env.cr.dbname,
            'master_pwd': 'admin',
            'backup_destination': 'google_drive',
            'gdrive_access_token': 'access_token',
            'google_drive_folder_key': 'folder_key',
            'gdrive_token_validity': fields.Datetime.now() + timedelta(days=1),
            'active': True,
        })

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'files': [{
                'name': 'gdrive_backup.zip',
                'webContentLink': 'https://drive.google.com/file',
                'createdTime': '2026-01-01T12:00:00Z',
            }]
        }

        with patch('odoo.addons.odoo_database_restore_manager.models.database_manager.request', self._get_mock_request()):
            with patch('requests.get', return_value=mock_response):
                res = self.DatabaseManager.action_import_files()
                self.assertIsInstance(res[0], dict)
                self.assertIn('gdrive_backup.zip', res[0])
                self.assertEqual(res[0]['gdrive_backup.zip'][1], 'Google Drive')

    def test_action_import_files_google_drive_exception(self):
        """Test action_import_files when Google Drive API raises an error."""
        self.env['ir.config_parameter'].set_param(
            'odoo_database_restore_manager.backup_count', '5'
        )
        self.BackupConfigure.create({
            'name': 'Google Drive Config',
            'db_name': self.env.cr.dbname,
            'master_pwd': 'admin',
            'backup_destination': 'google_drive',
            'gdrive_access_token': 'token',
            'google_drive_folder_key': 'folder',
            'gdrive_token_validity': fields.Datetime.now() + timedelta(days=1),
            'active': True,
        })

        with patch('odoo.addons.odoo_database_restore_manager.models.database_manager.request', self._get_mock_request()):
            with patch('requests.get', side_effect=Exception('GDrive Error')):
                res = self.DatabaseManager.action_import_files()
                self.assertEqual(res[0], 'error')
                self.assertEqual(res[2], 'Google Drive')

    def test_action_import_files_ftp_destination(self):
        """Test action_import_files with FTP storage destination."""
        self.env['ir.config_parameter'].set_param(
            'odoo_database_restore_manager.backup_count', '5'
        )
        self.BackupConfigure.create({
            'name': 'FTP Config',
            'db_name': self.env.cr.dbname,
            'master_pwd': 'admin',
            'backup_destination': 'ftp',
            'ftp_host': 'ftp.example.com',
            'ftp_port': '21',
            'ftp_user': 'user',
            'ftp_password': 'password',
            'ftp_path': '/backups',
            'active': True,
        })

        mock_ftp = MagicMock()
        mock_ftp.nlst.return_value = ['/backups/ftp_backup.zip']
        mock_ftp.voidcmd.return_value = '213 20260101120000'

        with patch('odoo.addons.odoo_database_restore_manager.models.database_manager.request', self._get_mock_request()):
            with patch('ftplib.FTP', return_value=mock_ftp):
                res = self.DatabaseManager.action_import_files()
                self.assertIsInstance(res[0], dict)
                self.assertIn('ftp_backup.zip', res[0])
                self.assertEqual(res[0]['ftp_backup.zip'][1], 'FTP Storage')

    def test_action_import_files_ftp_exception(self):
        """Test action_import_files when FTP connection fails."""
        self.env['ir.config_parameter'].set_param(
            'odoo_database_restore_manager.backup_count', '5'
        )
        self.BackupConfigure.create({
            'name': 'FTP Config',
            'db_name': self.env.cr.dbname,
            'master_pwd': 'admin',
            'backup_destination': 'ftp',
            'ftp_host': 'ftp.example.com',
            'ftp_port': '21',
            'ftp_user': 'user',
            'ftp_password': 'password',
            'ftp_path': '/backups',
            'active': True,
        })

        with patch('odoo.addons.odoo_database_restore_manager.models.database_manager.request', self._get_mock_request()):
            with patch('ftplib.FTP', side_effect=Exception('FTP Connection Error')):
                res = self.DatabaseManager.action_import_files()
                self.assertEqual(res[0], 'error')
                self.assertEqual(res[2], 'FTP server')

    def test_action_import_files_sftp_destination(self):
        """Test action_import_files with SFTP storage destination."""
        self.env['ir.config_parameter'].set_param(
            'odoo_database_restore_manager.backup_count', '5'
        )
        self.BackupConfigure.create({
            'name': 'SFTP Config',
            'db_name': self.env.cr.dbname,
            'master_pwd': 'admin',
            'backup_destination': 'sftp',
            'sftp_host': 'sftp.example.com',
            'sftp_port': '22',
            'sftp_user': 'user',
            'sftp_password': 'password',
            'sftp_path': '/backups',
            'active': True,
        })

        mock_stat = MagicMock()
        mock_stat.st_mtime = 1700000000

        mock_sftp_server = MagicMock()
        mock_sftp_server.listdir.return_value = ['sftp_backup.zip']
        mock_sftp_server.stat.return_value = mock_stat

        mock_sftp_client = MagicMock()
        mock_sftp_client.open_sftp.return_value = mock_sftp_server

        with patch('odoo.addons.odoo_database_restore_manager.models.database_manager.request', self._get_mock_request()):
            with patch('paramiko.SSHClient', return_value=mock_sftp_client):
                res = self.DatabaseManager.action_import_files()
                self.assertIsInstance(res[0], dict)
                self.assertIn('sftp_backup.zip', res[0])
                self.assertEqual(res[0]['sftp_backup.zip'][1], 'SFTP Storage')

    def test_action_import_files_sftp_exception(self):
        """Test action_import_files when SFTP connection fails."""
        self.env['ir.config_parameter'].set_param(
            'odoo_database_restore_manager.backup_count', '5'
        )
        self.BackupConfigure.create({
            'name': 'SFTP Config',
            'db_name': self.env.cr.dbname,
            'master_pwd': 'admin',
            'backup_destination': 'sftp',
            'sftp_host': 'sftp.example.com',
            'sftp_port': '22',
            'sftp_user': 'user',
            'sftp_password': 'password',
            'sftp_path': '/backups',
            'active': True,
        })

        mock_sftp_client = MagicMock()
        mock_sftp_client.connect.side_effect = Exception('SFTP Error')

        with patch('odoo.addons.odoo_database_restore_manager.models.database_manager.request', self._get_mock_request()):
            with patch('paramiko.SSHClient', return_value=mock_sftp_client):
                res = self.DatabaseManager.action_import_files()
                self.assertEqual(res[0], 'error')
                self.assertEqual(res[2], 'SFTP server')

    def test_action_import_files_nextcloud_destination(self):
        """Test action_import_files with Nextcloud storage destination."""
        self.env['ir.config_parameter'].set_param(
            'odoo_database_restore_manager.backup_count', '5'
        )
        self.BackupConfigure.create({
            'name': 'Nextcloud Config',
            'db_name': self.env.cr.dbname,
            'master_pwd': 'admin',
            'backup_destination': 'next_cloud',
            'domain': 'https://nextcloud.example.com',
            'next_cloud_user_name': 'user',
            'next_cloud_password': 'password',
            'nextcloud_folder_key': 'backups',
            'active': True,
        })

        mock_file = MagicMock()
        mock_file.name = 'nextcloud_backup.zip'

        mock_share = MagicMock()
        mock_share.get_link.return_value = 'https://nextcloud.example.com/s/link'

        mock_file_info = MagicMock()
        mock_file_info.attributes = {'{DAV:}getlastmodified': 'Wed, 01 Jan 2026 12:00:00 GMT'}

        mock_nc = MagicMock()
        mock_nc.list.return_value = [mock_file]
        mock_nc.share_file_with_link.return_value = mock_share
        mock_nc.file_info.return_value = mock_file_info

        with patch('odoo.addons.odoo_database_restore_manager.models.database_manager.request', self._get_mock_request()):
            with patch('nextcloud_client.Client', return_value=mock_nc):
                res = self.DatabaseManager.action_import_files()
                self.assertIsInstance(res[0], dict)
                self.assertIn('nextcloud_backup.zip', res[0])
                self.assertEqual(res[0]['nextcloud_backup.zip'][1], 'Nextcloud')

    def test_action_import_files_nextcloud_exception(self):
        """Test action_import_files when Nextcloud client raises an error."""
        self.env['ir.config_parameter'].set_param(
            'odoo_database_restore_manager.backup_count', '5'
        )
        self.BackupConfigure.create({
            'name': 'Nextcloud Config',
            'db_name': self.env.cr.dbname,
            'master_pwd': 'admin',
            'backup_destination': 'next_cloud',
            'domain': 'https://nextcloud.example.com',
            'next_cloud_user_name': 'user',
            'next_cloud_password': 'password',
            'nextcloud_folder_key': 'backups',
            'active': True,
        })

        with patch('odoo.addons.odoo_database_restore_manager.models.database_manager.request', self._get_mock_request()):
            with patch('nextcloud_client.Client', side_effect=Exception('Nextcloud Error')):
                res = self.DatabaseManager.action_import_files()
                self.assertEqual(res[0], 'error')
                self.assertEqual(res[2], 'Nextcloud')

    def test_action_import_files_amazon_s3_destination(self):
        """Test action_import_files with Amazon S3 storage destination."""
        self.env['ir.config_parameter'].set_param(
            'odoo_database_restore_manager.backup_count', '5'
        )
        self.BackupConfigure.create({
            'name': 'S3 Config',
            'db_name': self.env.cr.dbname,
            'master_pwd': 'admin',
            'backup_destination': 'amazon_s3',
            'aws_access_key': 'access_key',
            'aws_secret_access_key': 'secret_key',
            'bucket_file_name': 'mybucket',
            'aws_folder_name': 'backups',
            'active': True,
        })

        mock_boto_client = MagicMock()
        mock_boto_client.get_bucket_location.return_value = {'LocationConstraint': 'us-east-1'}
        mock_boto_client.list_objects.return_value = {
            'Contents': [{
                'Key': 'backups/s3_backup.zip',
                'Size': 1024,
                'LastModified': '2026-01-01 12:00:00',
            }]
        }
        mock_boto_client.generate_presigned_url.return_value = 'https://s3.amazonaws.com/url'

        with patch('odoo.addons.odoo_database_restore_manager.models.database_manager.request', self._get_mock_request()):
            with patch('boto3.client', return_value=mock_boto_client):
                res = self.DatabaseManager.action_import_files()
                self.assertIsInstance(res[0], dict)
                self.assertIn('backups/s3_backup.zip', res[0])
                self.assertEqual(res[0]['backups/s3_backup.zip'][1], 'AmazonS3')

    def test_action_import_files_amazon_s3_exception(self):
        """Test action_import_files when Amazon S3 client raises an error."""
        self.env['ir.config_parameter'].set_param(
            'odoo_database_restore_manager.backup_count', '5'
        )
        self.BackupConfigure.create({
            'name': 'S3 Config',
            'db_name': self.env.cr.dbname,
            'master_pwd': 'admin',
            'backup_destination': 'amazon_s3',
            'aws_access_key': 'access_key',
            'aws_secret_access_key': 'secret_key',
            'bucket_file_name': 'mybucket',
            'aws_folder_name': 'backups',
            'active': True,
        })

        with patch('odoo.addons.odoo_database_restore_manager.models.database_manager.request', self._get_mock_request()):
            with patch('boto3.client', side_effect=Exception('S3 Error')):
                res = self.DatabaseManager.action_import_files()
                self.assertEqual(res[0], 'error')
                self.assertEqual(res[2], 'Amazon S3')
