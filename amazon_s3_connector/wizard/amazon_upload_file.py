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
import boto3

from odoo import fields, models
from odoo.exceptions import ValidationError


class AmazonUploadFile(models.TransientModel):
    """Wizard to upload a file to the Amazon S3 bucket"""
    _name = "amazon.upload.file"
    _description = "Amazon Upload File"

    file = fields.Binary(string="Attachment", help="Select a file to upload")
    file_name = fields.Char(help="Name of the file to upload")

    def action_amazon_upload(self):
        """
        Uploads file to Amazon S3
        """
        self.ensure_one()
        if not self.file:
            raise ValidationError(
                self.env._("Please select a file to upload."))
        credentials = self.env['amazon.dashboard']._get_s3_credentials()
        if not credentials:
            raise ValidationError(self.env._(
                "Amazon S3 is not configured. Enable it and enter the "
                "credentials in Settings > Integrations.",
            ))
        access_key, secret_key, bucket_name = credentials
        try:
            client = boto3.resource(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
            )
            client.Bucket(bucket_name).put_object(
                Key=self.file_name or "uploaded_file",
                Body=self.file.content,
            )
        except Exception as e:
            raise ValidationError(
                self.env._('Failed to upload the file (%s)', e)) from e
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': self.env._('The file has been uploaded.'),
                'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'},
            },
        }
