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
import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from odoo import api, models


class AmazonDashboard(models.AbstractModel):
    """Read the files of the configured Amazon S3 bucket"""
    _name = 'amazon.dashboard'
    _description = "Amazon S3 Dashboard"

    @api.model
    def _get_s3_credentials(self):
        """Return (access key, secret key, bucket), or False when the
        connector is disabled or not fully configured"""
        params = self.env['ir.config_parameter'].sudo()
        if not params.get_bool('amazon_s3_connector.amazon_connector'):
            return False
        credentials = (
            params.get_str('amazon_s3_connector.amazon_access_key'),
            params.get_str('amazon_s3_connector.amazon_secret_key'),
            params.get_str('amazon_s3_connector.amazon_bucket_name'),
        )
        return credentials if all(credentials) else False

    @api.model
    def amazon_view_files(self, *args, **kwargs):
        """
        Return the files of the configured Amazon S3 bucket.

        :return: a list of [name, pre-signed URL, size, last modified date,
                 file type] for every non-empty object, ['e', message] when
                 Amazon S3 returns an error, or False when the connector is
                 not configured.
        """
        credentials = self._get_s3_credentials()
        if not credentials:
            return False
        access_key, secret_key, bucket_name = credentials
        try:
            client = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
            )
            region = client.get_bucket_location(Bucket=bucket_name)
            region_name = region.get('LocationConstraint') or 'us-east-1'

            client = boto3.client(
                's3',
                region_name=region_name,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
            )
            # A single call returns at most 1000 objects
            pages = client.get_paginator('list_objects_v2').paginate(
                Bucket=bucket_name)
            files = []
            for data in (obj for page in pages
                         for obj in page.get('Contents', [])):
                if data['Size'] == 0:
                    continue
                url = client.generate_presigned_url(
                    ClientMethod='get_object',
                    Params={
                        'Bucket': bucket_name,
                        'Key': data['Key'],
                    },
                )
                size_kb = data['Size'] / 1024
                if size_kb > 1024:
                    size = f"{round(size_kb / 1024, 1)} MB"
                else:
                    size = f"{round(size_kb, 1)} KB"
                file_type = os.path.splitext(
                    data['Key'])[1].replace('.', '').upper()
                files.append([
                    data['Key'],                    # name
                    url,                            # url
                    size,                           # size
                    str(data['LastModified']),      # date
                    file_type,                       # type
                ])
            return files
        except (BotoCoreError, ClientError) as e:
            return ['e', str(e)]
