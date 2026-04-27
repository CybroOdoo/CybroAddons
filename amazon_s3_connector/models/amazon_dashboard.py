# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
import boto3
import os
from odoo import models


class AmazonDashboard(models.Model):
    """Model for displaying and managing files stored in an Amazon S3 bucket."""
    _name = 'amazon.dashboard'
    _description = "Amazon S3 Dashboard"

    def amazon_view_files(self):
        """
            Retrieve files from the configured Amazon S3 bucket with
            pre-signed URLs, size, last modified date, and file type.
            Returns False if configuration is missing or an error list on failure.
            """
        access_key = self.env['ir.config_parameter'].sudo().get_param(
            'amazon_s3_connector.amazon_access_key')
        secret_key = self.env['ir.config_parameter'].sudo().get_param(
            'amazon_s3_connector.amazon_secret_key')
        bucket_name = self.env['ir.config_parameter'].sudo().get_param(
            'amazon_s3_connector.amazon_bucket_name')

        if not access_key or not secret_key or not bucket_name:
            return False

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

            response = client.list_objects_v2(Bucket=bucket_name)
            files = []

            for data in response.get('Contents', []):
                if data['Size'] == 0:
                    continue

                url = client.generate_presigned_url(
                    ClientMethod='get_object',
                    Params={
                        'Bucket': bucket_name,
                        'Key': data['Key']
                    }
                )

                size_kb = data['Size'] / 1024
                if size_kb > 1024:
                    size = f"{round(size_kb / 1024, 1)} MB"
                else:
                    size = f"{round(size_kb, 1)} KB"

                file_type = os.path.splitext(data['Key'])[1].replace('.', '').upper()

                files.append([
                    data['Key'],                    # name
                    url,                            # url
                    size,                           # size
                    str(data['LastModified']),      # date
                    file_type                       # type
                ])

            return files

        except Exception as e:
            return ['e', str(e)]
