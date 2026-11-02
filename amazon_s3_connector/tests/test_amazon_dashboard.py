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
from datetime import datetime
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

BOTO3_CLIENT = 'odoo.addons.amazon_s3_connector.models.amazon_dashboard.boto3.client'


@tagged('post_install', '-at_install')
class TestAmazonDashboard(TransactionCase):
    """Tests for listing Amazon S3 files on the dashboard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dashboard = cls.env['amazon.dashboard']

    def _set_credentials(self, access='ACCESS', secret='SECRET', bucket='my-bucket'):
        """Store the S3 credentials as system parameters."""
        params = self.env['ir.config_parameter'].sudo()
        params.set_bool('amazon_s3_connector.amazon_connector', True)
        params.set_str('amazon_s3_connector.amazon_access_key', access)
        params.set_str('amazon_s3_connector.amazon_secret_key', secret)
        params.set_str('amazon_s3_connector.amazon_bucket_name', bucket)

    def _mock_client(self, region=None, contents=None):
        """Return a mocked boto3 S3 client."""
        client = MagicMock()
        client.get_bucket_location.return_value = {'LocationConstraint': region}
        client.get_paginator.return_value.paginate.return_value = [
            {'Contents': contents or []}]
        client.generate_presigned_url.side_effect = (
            lambda ClientMethod, Params: f"https://s3/{Params['Key']}")
        return client

    def test_no_credentials_returns_false(self):
        """Without credentials the dashboard returns False."""
        self._set_credentials(access='', secret='', bucket='')
        with patch(BOTO3_CLIENT) as mock_client:
            self.assertFalse(self.dashboard.amazon_view_files())
        mock_client.assert_not_called()

    def test_partial_credentials_returns_false(self):
        """A missing bucket name is treated as not configured."""
        self._set_credentials(bucket='')
        self.assertFalse(self.dashboard.amazon_view_files())

    def test_connector_disabled(self):
        """With the connector switched off, no files are listed."""
        self._set_credentials()
        self.env['ir.config_parameter'].sudo().set_bool(
            'amazon_s3_connector.amazon_connector', False)
        with patch(BOTO3_CLIENT) as mock_client:
            self.assertFalse(self.dashboard.amazon_view_files())
        mock_client.assert_not_called()

    def test_list_several_pages(self):
        """Buckets with more than one page of objects are fully listed."""
        self._set_credentials()
        modified = datetime(2026, 1, 1, 10, 0, 0)
        client = self._mock_client()
        client.get_paginator.return_value.paginate.return_value = [
            {'Contents': [{'Key': 'a.txt', 'Size': 10, 'LastModified': modified}]},
            {'Contents': [{'Key': 'b.txt', 'Size': 10, 'LastModified': modified}]},
            {},
        ]
        with patch(BOTO3_CLIENT, return_value=client):
            files = self.dashboard.amazon_view_files()
        self.assertEqual([f[0] for f in files], ['a.txt', 'b.txt'])

    def test_list_files(self):
        """Files are returned with name, url, size, date and type."""
        self._set_credentials()
        modified = datetime(2026, 1, 1, 10, 0, 0)
        client = self._mock_client(contents=[
            {'Key': 'report.pdf', 'Size': 2048, 'LastModified': modified},
            {'Key': 'video.mp4', 'Size': 3 * 1024 * 1024, 'LastModified': modified},
            {'Key': 'folder/', 'Size': 0, 'LastModified': modified},
        ])
        with patch(BOTO3_CLIENT, return_value=client):
            files = self.dashboard.amazon_view_files()
        self.assertEqual(files, [
            ['report.pdf', 'https://s3/report.pdf', '2.0 KB', str(modified), 'PDF'],
            ['video.mp4', 'https://s3/video.mp4', '3.0 MB', str(modified), 'MP4'],
        ])
        client.get_paginator.assert_called_once_with('list_objects_v2')
        client.get_paginator.return_value.paginate.assert_called_once_with(
            Bucket='my-bucket')

    def test_default_region(self):
        """A bucket without location constraint uses us-east-1."""
        self._set_credentials()
        client = self._mock_client(region=None)
        with patch(BOTO3_CLIENT, return_value=client) as mock_client:
            self.dashboard.amazon_view_files()
        self.assertEqual(mock_client.call_args.kwargs['region_name'], 'us-east-1')

    def test_bucket_region(self):
        """The bucket's own region is used for the second client."""
        self._set_credentials()
        client = self._mock_client(region='eu-west-1')
        with patch(BOTO3_CLIENT, return_value=client) as mock_client:
            self.dashboard.amazon_view_files()
        self.assertEqual(mock_client.call_args.kwargs['region_name'], 'eu-west-1')
        self.assertEqual(mock_client.call_args.kwargs['aws_access_key_id'], 'ACCESS')
        self.assertEqual(mock_client.call_args.kwargs['aws_secret_access_key'], 'SECRET')

    def test_empty_bucket(self):
        """An empty bucket returns an empty list."""
        self._set_credentials()
        with patch(BOTO3_CLIENT, return_value=self._mock_client()):
            self.assertEqual(self.dashboard.amazon_view_files(), [])

    def test_error_is_returned(self):
        """S3 errors are returned as ['e', message]."""
        self._set_credentials()
        client = self._mock_client()
        client.get_bucket_location.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
            'GetBucketLocation')
        with patch(BOTO3_CLIENT, return_value=client):
            result = self.dashboard.amazon_view_files()
        self.assertEqual(result[0], 'e')
        self.assertIn('Access Denied', result[1])
