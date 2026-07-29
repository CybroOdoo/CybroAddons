# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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

from tempfile import NamedTemporaryFile
from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('-at_install', 'post_install')
class TestAmazonBucket(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env['ir.config_parameter'].sudo()
        cls.config.set_param(
            'amazon_forecast_integration.amazon_forecast', '1')
        cls.config.set_param(
            'amazon_forecast_integration.amazon_access_key', 'access-key')
        cls.config.set_param(
            'amazon_forecast_integration.amazon_secret_access_key',
            'secret-key')
        cls.config.set_param(
            'amazon_forecast_integration.amazon_region', 'ap-south-1')

    def test_validate_bucket_name_accepts_valid_name(self):
        bucket = self.env['amazon.bucket'].new({
            'bucket_name': 'valid-bucket-name',
        })

        self.assertIsNone(bucket._validate_bucket_name(bucket.bucket_name))

    def test_validate_bucket_name_rejects_invalid_names(self):
        bucket = self.env['amazon.bucket'].new({'bucket_name': 'valid-name'})

        invalid_names = [
            'ab',
            'InvalidName',
            '-starts-with-hyphen',
            'ends-with-hyphen-',
            'name..with-dots',
            '192.168.0.1',
            'xn--reserved',
            'bucket-s3alias',
            'bucket.with.dot',
        ]
        for bucket_name in invalid_names:
            with self.subTest(bucket_name=bucket_name):
                with self.assertRaises(ValueError):
                    bucket._validate_bucket_name(bucket_name)

    def test_action_s3bucket_creates_bucket_and_updates_state(self):
        fetch_record = self.env['amazon.fetch.data'].create({
            'url': 'http://example.test',
            'db_name': 'test_db',
            'db_username': 'admin',
            'db_password': 'admin',
            'csv_file_path': '/tmp/forecast.csv',
        })
        bucket = self.env['amazon.bucket'].create({
            'bucket_name': 'forecast-bucket',
        })
        s3_client = MagicMock()
        session = MagicMock()
        session.client.return_value = s3_client

        with patch(
            'odoo.addons.amazon_forecast_integration.models.amazon_bucket.'
            'boto3.Session',
            return_value=session,
        ):
            bucket.action_s3bucket()

        session.client.assert_called_once_with('s3')
        s3_client.create_bucket.assert_called_once_with(
            Bucket='forecast-bucket',
            CreateBucketConfiguration={'LocationConstraint': 'ap-south-1'},
        )
        self.assertEqual(bucket.file_path, fetch_record.csv_file_path)
        self.assertEqual(bucket.state, 'push_to_bucket')

    def test_action_s3bucket_wraps_invalid_bucket_name(self):
        self.env['amazon.fetch.data'].create({
            'url': 'http://example.test',
            'db_name': 'test_db',
            'db_username': 'admin',
            'db_password': 'admin',
            'csv_file_path': '/tmp/forecast.csv',
        })
        bucket = self.env['amazon.bucket'].create({
            'bucket_name': 'invalid.bucket',
        })

        with self.assertRaises(UserError):
            bucket.action_s3bucket()

    def test_action_s3bucket_push_uploads_file_and_sets_s3_uri(self):
        with NamedTemporaryFile() as csv_file:
            csv_file.write(b'item_id,timestamp,demand\nA,2026-01-01,3\n')
            csv_file.flush()
            bucket = self.env['amazon.bucket'].create({
                'bucket_name': 'forecast-bucket',
                'file_path': csv_file.name,
                'state': 'push_to_bucket',
            })
            s3_client = MagicMock()
            bucket_resource = MagicMock()
            bucket_resource.objects.all.return_value = [
                MagicMock(key='forecast.csv')
            ]
            s3_resource = MagicMock()
            s3_resource.Bucket.return_value = bucket_resource
            session = MagicMock()
            session.client.return_value = s3_client
            session.resource.return_value = s3_resource

            with patch(
                'odoo.addons.amazon_forecast_integration.models.'
                'amazon_bucket.boto3.Session',
                return_value=session,
            ):
                bucket.action_s3bucket_push()

        s3_client.put_object.assert_called_once()
        self.assertEqual(bucket.s3_uri, 's3://forecast-bucket/forecast.csv')
        self.assertEqual(bucket.state, 'pushed')
