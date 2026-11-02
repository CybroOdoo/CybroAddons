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
import base64
from unittest.mock import MagicMock, patch

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

BOTO3_RESOURCE = 'odoo.addons.amazon_s3_connector.wizard.amazon_upload_file.boto3.resource'


@tagged('post_install', '-at_install')
class TestAmazonUploadFile(TransactionCase):
    """Tests for the upload to Amazon S3 wizard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.content = b'Hello Amazon S3'
        params = cls.env['ir.config_parameter'].sudo()
        params.set_bool('amazon_s3_connector.amazon_connector', True)
        params.set_str('amazon_s3_connector.amazon_access_key', 'ACCESS')
        params.set_str('amazon_s3_connector.amazon_secret_key', 'SECRET')
        params.set_str('amazon_s3_connector.amazon_bucket_name', 'my-bucket')

    def _create_wizard(self, file_name='hello.txt', content=None):
        """Create an upload wizard holding a file."""
        content = self.content if content is None else content
        return self.env['amazon.upload.file'].create({
            'file': base64.b64encode(content).decode() if content else False,
            'file_name': file_name,
        })

    def _uploaded(self, resource):
        """Return the Key and Body content sent to S3."""
        kwargs = resource.return_value.Bucket.return_value.put_object.call_args.kwargs
        body = kwargs['Body']
        if hasattr(body, 'read'):
            with body:
                body = body.read()
        return kwargs['Key'], body

    def test_upload_file(self):
        """The file is uploaded to the configured bucket."""
        wizard = self._create_wizard()
        with patch(BOTO3_RESOURCE) as resource:
            action = wizard.action_amazon_upload()
        resource.assert_called_once_with(
            's3', aws_access_key_id='ACCESS', aws_secret_access_key='SECRET')
        resource.return_value.Bucket.assert_called_once_with('my-bucket')
        self.assertEqual(self._uploaded(resource), ('hello.txt', self.content))
        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(action['params']['type'], 'success')

    def test_upload_without_file_name(self):
        """A file without name is uploaded as 'uploaded_file'."""
        wizard = self._create_wizard(file_name=False)
        with patch(BOTO3_RESOURCE) as resource:
            wizard.action_amazon_upload()
        self.assertEqual(self._uploaded(resource)[0], 'uploaded_file')

    def test_upload_without_file(self):
        """Uploading without a file raises an error."""
        wizard = self._create_wizard(content=b'')
        with patch(BOTO3_RESOURCE) as resource, self.assertRaises(ValidationError):
            wizard.action_amazon_upload()
        resource.assert_not_called()

    def test_upload_without_credentials(self):
        """Uploading without credentials raises an error."""
        self.env['ir.config_parameter'].sudo().set_str(
            'amazon_s3_connector.amazon_bucket_name', '')
        wizard = self._create_wizard()
        with patch(BOTO3_RESOURCE) as resource, self.assertRaises(ValidationError):
            wizard.action_amazon_upload()
        resource.assert_not_called()

    def test_upload_connector_disabled(self):
        """Uploading with the connector switched off raises an error."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'amazon_s3_connector.amazon_connector', False)
        wizard = self._create_wizard()
        with patch(BOTO3_RESOURCE) as resource, self.assertRaises(ValidationError):
            wizard.action_amazon_upload()
        resource.assert_not_called()

    def test_upload_error(self):
        """S3 errors are raised as a ValidationError with the reason."""
        wizard = self._create_wizard()
        bucket = MagicMock()
        bucket.put_object.side_effect = Exception('Access Denied')
        with patch(BOTO3_RESOURCE) as resource:
            resource.return_value.Bucket.return_value = bucket
            with self.assertRaisesRegex(ValidationError, 'Access Denied'):
                wizard.action_amazon_upload()
