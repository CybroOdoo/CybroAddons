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
from unittest.mock import MagicMock, patch

import odoo
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestDatabaseRestore(TransactionCase):
    """Test suite for database.restore wizard model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.DataBaseRestore = cls.env['database.restore']
        cls.BackupConfigure = cls.env['db.backup.configure']

    def setUp(self):
        super().setUp()
        self.check_cred_patcher = patch(
            'odoo.addons.auto_database_backup.models.db_backup_configure.DbBackupConfigure._check_db_credentials',
            return_value=True
        )
        self.check_cred_patcher.start()
        self.addCleanup(self.check_cred_patcher.stop)
        self.BackupConfigure.with_context(active_test=False).search([]).unlink()

    def test_action_restore_database_local_storage(self):
        """Test action_restore_database with Local Storage location."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            f.write(b'dummy zip content')
            temp_file_path = f.name

        try:
            wizard = self.DataBaseRestore.create({
                'db_file': temp_file_path,
                'db_name': 'restored_local_db',
                'db_master_pwd': 'admin_password',
                'backup_location': 'Local Storage',
            })

            with patch('odoo.service.db.check_super') as mock_check_super:
                with patch('odoo.service.db.restore_db') as mock_restore_db:
                    res = wizard.action_restore_database(copy=False)
                    mock_check_super.assert_called_once_with('admin_password')
                    mock_restore_db.assert_called_once_with('restored_local_db', temp_file_path, False)
                    self.assertEqual(res, {
                        'type': 'ir.actions.act_url',
                        'url': '/web/database/manager'
                    })
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def test_action_restore_database_google_drive(self):
        """Test action_restore_database with Google Drive location."""
        wizard = self.DataBaseRestore.create({
            'db_file': 'https://drive.google.com/uc?id=12345',
            'db_name': 'restored_gdrive_db',
            'db_master_pwd': 'admin_password',
            'backup_location': 'Google Drive',
        })

        with patch('odoo.service.db.check_super'):
            with patch('odoo.service.db.restore_db') as mock_restore_db:
                with patch('gdown.download') as mock_gdown:
                    res = wizard.action_restore_database(copy=True)
                    mock_gdown.assert_called_once()
                    mock_restore_db.assert_called_once()
                    self.assertEqual(res.get('type'), 'ir.actions.act_url')

    def test_action_restore_database_dropbox_onedrive(self):
        """Test action_restore_database with Dropbox / OneDrive / HTTP stream location."""
        wizard = self.DataBaseRestore.create({
            'db_file': 'https://example.com/backup.zip',
            'db_name': 'restored_dropbox_db',
            'db_master_pwd': 'admin_password',
            'backup_location': 'Dropbox',
        })

        mock_response = MagicMock()
        mock_response.content = b'mock backup zip stream'

        with patch('odoo.service.db.check_super'):
            with patch('odoo.service.db.restore_db') as mock_restore_db:
                with patch('requests.get', return_value=mock_response) as mock_get:
                    res = wizard.action_restore_database()
                    mock_get.assert_called_once_with('https://example.com/backup.zip', stream=True)
                    mock_restore_db.assert_called_once()
                    self.assertEqual(res.get('type'), 'ir.actions.act_url')

    def test_action_restore_database_ftp_storage(self):
        """Test action_restore_database with FTP Storage location."""
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

        wizard = self.DataBaseRestore.create({
            'db_file': '/backups/ftp_backup.zip',
            'db_name': 'restored_ftp_db',
            'db_master_pwd': 'admin_password',
            'backup_location': 'FTP Storage',
        })

        mock_ftp = MagicMock()

        with patch('odoo.service.db.check_super'):
            with patch('odoo.service.db.restore_db') as mock_restore_db:
                with patch('ftplib.FTP', return_value=mock_ftp):
                    res = wizard.action_restore_database()
                    mock_ftp.connect.assert_called_once_with('ftp.example.com', 21)
                    mock_ftp.login.assert_called_once_with('user', 'password')
                    mock_restore_db.assert_called_once()
                    self.assertEqual(res.get('type'), 'ir.actions.act_url')

    def test_action_restore_database_sftp_storage(self):
        """Test action_restore_database with SFTP Storage location."""
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

        wizard = self.DataBaseRestore.create({
            'db_file': '/backups/sftp_backup.zip',
            'db_name': 'restored_sftp_db',
            'db_master_pwd': 'admin_password',
            'backup_location': 'SFTP Storage',
        })

        mock_sftp_server = MagicMock()
        mock_sftp_client = MagicMock()
        mock_sftp_client.open_sftp.return_value = mock_sftp_server

        with patch('odoo.service.db.check_super'):
            with patch('odoo.service.db.restore_db') as mock_restore_db:
                with patch('paramiko.SSHClient', return_value=mock_sftp_client):
                    res = wizard.action_restore_database()
                    mock_sftp_client.connect.assert_called_once_with(
                        hostname='sftp.example.com', username='user', password='password', port='22'
                    )
                    mock_sftp_server.getfo.assert_called_once()
                    mock_restore_db.assert_called_once()
                    self.assertEqual(res.get('type'), 'ir.actions.act_url')

    def test_action_restore_database_insecure_admin_password(self):
        """Test action_restore_database when admin password is verified as insecure."""
        wizard = self.DataBaseRestore.create({
            'db_file': '/tmp/dummy.zip',
            'db_name': 'restored_db',
            'db_master_pwd': 'new_master_password',
            'backup_location': 'Local Storage',
        })

        with patch.object(odoo.tools.config, 'verify_admin_password', return_value=True):
            with patch('odoo.addons.odoo_database_restore_manager.wizard.database_restore.dispatch_rpc') as mock_dispatch:
                with patch('odoo.service.db.check_super'):
                    with patch('odoo.service.db.restore_db'):
                        wizard.action_restore_database()
                        mock_dispatch.assert_called_once_with(
                            'db', 'change_admin_password', ["admin", "new_master_password"]
                        )

    def test_action_restore_database_exception_raises_user_error(self):
        """Test action_restore_database raises UserError when restoration process encounters an exception."""
        wizard = self.DataBaseRestore.create({
            'db_file': '/tmp/non_existent_file.zip',
            'db_name': 'fail_db',
            'db_master_pwd': 'wrong_password',
            'backup_location': 'Local Storage',
        })

        with patch('odoo.service.db.check_super', side_effect=Exception('Invalid master password')):
            with self.assertRaises(UserError) as cm:
                wizard.action_restore_database()
            self.assertIn("Database restore error: Invalid master password", str(cm.exception))
