# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from unittest.mock import patch

from odoo.addons.auto_database_backup.controllers.auto_database_backup \
    import OnedriveAuth
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

MODEL_PATH = 'odoo.addons.auto_database_backup.models.db_backup_configure'
MAIL_SEND = 'odoo.addons.mail.models.mail_template.MailTemplate.send_mail'


class TestDbBackupConfigure(TransactionCase):
    """Tests for the db.backup.configure model."""

    def setUp(self):
        super().setUp()
        self.Backup = self.env['db.backup.configure']
        self.db_name = self.env.cr.dbname
        # The scheduled backup never needs the master password, and cloud
        # calls are network-bound; here we only stub the two authorization
        # helpers so records can be created without a live master password.
        list_patch = patch('odoo.service.db.list_dbs',
                           return_value=[self.db_name])
        super_patch = patch('odoo.service.db.check_super', return_value=True)
        self.addCleanup(list_patch.stop)
        self.addCleanup(super_patch.stop)
        list_patch.start()
        super_patch.start()

    def _create_config(self, **vals):
        values = {
            'name': 'Test Backup',
            'db_name': self.db_name,
            'master_pwd': 'admin',
            'backup_destination': 'local',
            'backup_frequency': 'daily',
            'backup_path': '/tmp/adb_test',
        }
        values.update(vals)
        return self.Backup.create(values)

    def test_01_master_pwd_not_stored(self):
        """The master password is validated but never persisted."""
        config = self._create_config()
        self.assertTrue(config.id)
        self.assertFalse(
            config.master_pwd,
            "The master password must not be stored on the record.")

    def test_02_master_pwd_required_on_create(self):
        """Creating a configuration without a master password is rejected."""
        with self.assertRaises(ValidationError):
            self._create_config(master_pwd=False)

    def test_03_invalid_master_pwd_rejected(self):
        """An invalid master password raises a validation error."""
        with patch('odoo.service.db.check_super',
                   side_effect=Exception('bad password')):
            with self.assertRaises(ValidationError):
                self._create_config(master_pwd='wrong')

    def test_04_invalid_db_name_rejected(self):
        """A database name that does not exist is rejected."""
        with patch('odoo.service.db.list_dbs', return_value=['other_db']):
            with self.assertRaises(ValidationError):
                self._create_config(db_name='does_not_exist')

    def test_05_token_generated_flags(self):
        """The token-generated boolean flags reflect the stored tokens."""
        config = self._create_config()
        self.assertFalse(config.is_google_drive_token_generated)
        config.write({
            'gdrive_access_token': 'access',
            'gdrive_refresh_token': 'refresh',
        })
        self.assertTrue(config.is_google_drive_token_generated)
        config.write({'dropbox_refresh_token': 'dbx'})
        self.assertTrue(config.is_dropbox_token_generated)
        config.write({
            'onedrive_access_token': 'a',
            'onedrive_refresh_token': 'r',
        })
        self.assertTrue(config.is_onedrive_token_generated)

    def test_06_redirect_uri_compute(self):
        """The redirect URIs are computed from the instance base URL."""
        config = self._create_config()
        self.assertTrue(
            config.onedrive_redirect_uri.endswith('/onedrive/authentication'))
        self.assertTrue(
            config.gdrive_redirect_uri.endswith(
                '/google_drive/authentication'))

    def test_07_schedule_dispatches_to_handler(self):
        """_schedule_auto_backup dispatches active records to the right
        per-destination handler."""
        config = self._create_config(active=True)
        with patch.object(type(config), '_backup_to_local') as handler:
            self.Backup._schedule_auto_backup('daily')
            self.assertTrue(handler.called,
                            "The local backup handler should be called.")
        self.assertTrue(config.backup_filename)
        self.assertIn(self.db_name, config.backup_filename)

    def test_08_gdrive_token_validity_guard(self):
        """A never-generated Google Drive token must not crash the backup
        (previously ``False <= datetime`` raised a TypeError)."""
        config = self._create_config(
            backup_destination='google_drive',
            gdrive_token_validity=False,
        )
        with patch.object(type(config), 'generate_gdrive_refresh_token') \
                as refresh, \
                patch.object(type(config), 'dump_data'), \
                patch('%s.requests' % MODEL_PATH):
            config._backup_to_google_drive(config.db_name, 'backup.zip',
                                           'time')
            self.assertTrue(
                refresh.called,
                "An expired/missing token should trigger a refresh.")

    def test_09_dump_db_manifest(self):
        """The dump manifest contains the expected metadata."""
        config = self._create_config()
        manifest = config._dump_db_manifest(self.env.cr)
        self.assertEqual(manifest['db_name'], self.db_name)
        self.assertEqual(manifest['odoo_dump'], '1')
        self.assertIn('modules', manifest)
        self.assertIsInstance(manifest['modules'], dict)

    def test_10_s3_connection_missing_credentials(self):
        """The S3 connection test returns a danger notification when the
        credentials are missing."""
        config = self._create_config(backup_destination='amazon_s3')
        result = config.action_s3cloud()
        self.assertEqual(result['params']['type'], 'danger')

    def test_11_oauth_redirect_blocks_external_url(self):
        """The OAuth callback must not redirect to an external URL."""
        base_url = 'https://my-odoo.example.com'
        # An external url_return is refused in favour of the web client.
        self.assertEqual(
            OnedriveAuth._safe_redirect_url('https://evil.example.com/x',
                                            base_url), '/web')
        # A blank url_return is refused too.
        self.assertEqual(
            OnedriveAuth._safe_redirect_url(False, base_url), '/web')
        # A local url_return is preserved.
        local = base_url + '/web#id=1&model=db.backup.configure'
        self.assertEqual(
            OnedriveAuth._safe_redirect_url(local, base_url), local)

    def test_12_notify_requires_recipient(self):
        """No email is sent when notify_user is set but user_id is empty."""
        config = self._create_config(notify_user=True, user_id=False)
        with patch(MAIL_SEND) as send_mail:
            config._notify(success=True)
            self.assertFalse(
                send_mail.called,
                "No email should be sent without a recipient user.")
        config.user_id = self.env.ref('base.user_admin').id
        with patch(MAIL_SEND) as send_mail:
            config._notify(success=True)
            self.assertTrue(send_mail.called)

    def test_13_schedule_only_active_configs(self):
        """Only active configurations are backed up by the scheduler."""
        active_config = self._create_config(active=True)
        self._create_config(name='Inactive', active=False)
        with patch.object(type(active_config), '_backup_to_local') as handler:
            self.Backup._schedule_auto_backup('daily')
            self.assertEqual(
                handler.call_count, 1,
                "Only the single active configuration should be backed up.")

    def test_14_run_backup_logs_history_success(self):
        """A successful run records a success history row and last status."""
        config = self._create_config()
        with patch.object(type(config), '_backup_to_local'):
            status = config._run_backup()
        self.assertEqual(status, 'success')
        self.assertEqual(config.last_backup_status, 'success')
        self.assertTrue(config.last_success_date)
        self.assertEqual(config.history_count, 1)
        history = config.history_ids
        self.assertEqual(history.status, 'success')
        self.assertEqual(history.backup_destination, 'local')

    def test_15_run_backup_logs_history_failure(self):
        """A failing run records a failed history row and stores the error."""
        config = self._create_config()
        with patch.object(type(config), '_backup_to_local',
                          side_effect=Exception('boom')):
            status = config._run_backup()
        self.assertEqual(status, 'failed')
        self.assertEqual(config.last_backup_status, 'failed')
        self.assertEqual(config.history_ids.status, 'failed')
        self.assertIn('boom', config.history_ids.message)
        self.assertIn('boom', config.generated_exception)

    def test_16_backup_now_action(self):
        """Backup Now runs the config and returns a success notification."""
        config = self._create_config()
        with patch.object(type(config), '_backup_to_local'):
            result = config.action_backup_now()
        self.assertEqual(result['params']['type'], 'success')
        self.assertEqual(config.last_backup_status, 'success')

    def test_18_s3_compatible_endpoint_kwargs(self):
        """A custom endpoint/region is passed to the boto3 client, while the
        default Amazon S3 setup passes neither."""
        default = self._create_config(
            backup_destination='amazon_s3', aws_access_key='k',
            aws_secret_access_key='s')
        kwargs = default._get_s3_client_kwargs()
        self.assertNotIn('endpoint_url', kwargs)
        self.assertNotIn('region_name', kwargs)

        compatible = self._create_config(
            backup_destination='amazon_s3', aws_access_key='k',
            aws_secret_access_key='s',
            aws_endpoint_url='https://s3.us-west-002.backblazeb2.com',
            aws_region='us-west-002')
        kwargs = compatible._get_s3_client_kwargs()
        self.assertEqual(kwargs['endpoint_url'],
                         'https://s3.us-west-002.backblazeb2.com')
        self.assertEqual(kwargs['region_name'], 'us-west-002')

    def test_19_azure_missing_credentials(self):
        """The Azure connection test returns a danger notification when the
        credentials are missing."""
        config = self._create_config(backup_destination='azure_blob')
        result = config.action_azure()
        self.assertEqual(result['params']['type'], 'danger')

    def test_20_azure_service_client(self):
        """The Azure service client uses the configured account name."""
        config = self._create_config(
            backup_destination='azure_blob',
            azure_account_name='myaccount',
            azure_account_key='dGVzdGtleQ==')
        service = config._get_azure_service()
        self.assertEqual(service.account_name, 'myaccount')

    def test_21_gcs_missing_credentials(self):
        """The GCS connection test returns a danger notification when the
        credentials are missing."""
        config = self._create_config(backup_destination='google_cloud')
        result = config.action_gcs()
        self.assertEqual(result['params']['type'], 'danger')

    def test_22_gcs_invalid_key(self):
        """An invalid service account key returns a danger notification."""
        config = self._create_config(
            backup_destination='google_cloud',
            gcs_service_account_key='not-a-json-key', gcs_bucket='my-bucket')
        result = config.action_gcs()
        self.assertEqual(result['params']['type'], 'danger')

    def test_23_webdav_missing_credentials(self):
        """The WebDAV connection test returns a danger notification when the
        credentials are missing."""
        config = self._create_config(backup_destination='webdav')
        result = config.action_webdav()
        self.assertEqual(result['params']['type'], 'danger')

    def test_24_webdav_client(self):
        """The WebDAV client is built from the configured credentials."""
        config = self._create_config(
            backup_destination='webdav',
            webdav_url='https://host/dav/', webdav_username='u',
            webdav_password='p')
        self.assertTrue(config._get_webdav_client())

    def test_25_download_backup_action(self):
        """The download action returns a URL action pointing to the config."""
        config = self._create_config()
        action = config.action_download_backup()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertIn('/auto_database_backup/download/%s' % config.id,
                      action['url'])

    def test_26_multi_db_target_list(self):
        """The target database list reflects the backup scope."""
        config = self._create_config()
        with patch('odoo.service.db.list_dbs',
                   return_value=['a', 'b', 'c']):
            config.write({'backup_scope': 'all'})
            self.assertEqual(set(config._get_target_databases()),
                             {'a', 'b', 'c'})
            config.write({'backup_scope': 'selected',
                          'selected_db_names': 'a, c'})
            self.assertEqual(config._get_target_databases(), ['a', 'c'])

    def test_27_multi_db_run_backs_up_each(self):
        """A multi-database run backs up every target and logs one history
        row per database."""
        config = self._create_config(active=True)
        with patch('odoo.service.db.list_dbs', return_value=['a', 'b']):
            config.write({'backup_scope': 'all'})
            with patch.object(type(config), '_backup_to_local') as handler:
                config._run_backup()
                self.assertEqual(handler.call_count, 2)
        self.assertEqual(config.history_count, 2)
        self.assertEqual(config.last_backup_status, 'success')
        self.assertEqual(set(config.history_ids.mapped('db_name')),
                         {'a', 'b'})

    def test_28_view_scheduled_actions_action(self):
        """The Schedule Actions button opens the three backup crons."""
        config = self._create_config()
        action = config.action_view_scheduled_actions()
        self.assertEqual(action['res_model'], 'ir.cron')
        self.assertEqual(len(action['domain'][0][2]), 3)

    def test_17_notify_mode_failure_skips_success_email(self):
        """notify_mode='failure' suppresses success emails but not failures."""
        config = self._create_config(
            notify_user=True,
            user_id=self.env.ref('base.user_admin').id,
            notify_mode='failure')
        with patch(MAIL_SEND) as send_mail:
            config._notify(success=True)
            self.assertFalse(send_mail.called)
        with patch(MAIL_SEND) as send_mail:
            config._notify(success=False)
            self.assertTrue(send_mail.called)
