# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Shafna K(odoo@cybrosys.com)
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
import boto3
import re
from odoo import fields, models
from odoo.exceptions import UserError


class AmazonBucket(models.Model):
    """Class to create an Amazon S3 bucket"""
    _name = "amazon.bucket"
    _description = "Amazon Bucket"
    _rec_name = "bucket_name"

    bucket_name = fields.Char(string="Bucket Name", required=True,
                              help="""Provide the bucket name.
                                          Eg:
                                          - docexamplebucket1
                                          - log-delivery-march-2020
                                          - my-hosted-content""")
    state = fields.Selection([
        ('create_bucket', 'Create Bucket'),
        ('push_to_bucket', 'Push To bucket'),
        ('pushed', 'Pushed')
    ], help="States of bucket creation.", string="State",
        default='create_bucket')
    file_path = fields.Char(string="File Path",
                            help="Provide the file path of your data.")
    s3_uri = fields.Char(string="S3 URI", help="After pushing the data to s3 "
                                               "Bucket, URI will be computed.")

    def _validate_bucket_name(self, bucket_name):
        if len(bucket_name) < 3 or len(bucket_name) > 63:
            raise ValueError("Bucket name must be between 3 and 63 characters"
                             " long")
        if not re.match("^[a-z0-9.-]+$", bucket_name):
            raise ValueError("Bucket name can consist only of lowercase "
                             "letters, numbers, dots, and hyphens")
        if not bucket_name[0].isalnum() or not bucket_name[-1].isalnum():
            raise ValueError("Bucket name must begin and end with a letter or"
                             " number")
        if ".." in bucket_name:
            raise ValueError("Bucket name must not contain two adjacent "
                             "periods")
        if re.match(r"^\d+\.\d+\.\d+\.\d+$", bucket_name):
            raise ValueError("Bucket name must not be formatted as an "
                             "IP address")
        reserved_prefixes = ['xn--', 'sthree-', 'sthree-configurator-']
        reserved_suffixes = ['-s3alias', '--ol-s3']
        for prefix in reserved_prefixes:
            if bucket_name.startswith(prefix):
                raise ValueError("Bucket name must not start with the "
                                 "prefix '{prefix}'")
        for suffix in reserved_suffixes:
            if bucket_name.endswith(suffix):
                raise ValueError("Bucket name must not end with the"
                                 " suffix '{suffix}'")
        if '.' in bucket_name:
            raise ValueError("Buckets used with Transfer Acceleration can't "
                             "have dots (.) in their names")

    def action_s3bucket(self):
        """Function to create an S3 bucket in Amazon"""
        file = self.env['amazon.fetch.data'].get_file_path()
        values = self.env['amazon.dataset'].forecast_values()
        amazon_forecast = values['amazon_forecast']
        if amazon_forecast:
            amazon_access_key = values['amazon_access_key']
            amazon_secret_access_key = values['amazon_secret_access_key']
            amazon_region = values['amazon_region']
            session = boto3.Session(
                aws_access_key_id=amazon_access_key,
                aws_secret_access_key=amazon_secret_access_key,
                region_name=amazon_region
            )
            s3_client = session.client('s3')
            bucket_name = self.bucket_name
            try:
                self._validate_bucket_name(bucket_name)
            except ValueError as e:
                raise UserError(e)
            self.write({
                'file_path': file
            })
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': 'ap-south-1'}
            )
            self.write({'state': "push_to_bucket"})

    def action_s3bucket_push(self):
        """To push the data to Amazon S3 bucket"""
        values = self.env['amazon.dataset'].forecast_values()
        amazon_forecast = values['amazon_forecast']
        if amazon_forecast:
            amazon_access_key = values['amazon_access_key']
            amazon_secret_access_key = values['amazon_secret_access_key']
            amazon_region = values['amazon_region']
            session = boto3.Session(
                aws_access_key_id=amazon_access_key,
                aws_secret_access_key=amazon_secret_access_key,
                region_name=amazon_region
            )
            s3_client = session.client('s3')
            s3_resource = session.resource('s3')
            bucket = s3_resource.Bucket(self.bucket_name)
            bucket_name = self.bucket_name
            file_path = self.file_path
            with open(file_path, 'rb') as file:
                s3_client.put_object(Body=file, Bucket=bucket_name,
                                     Key=file_path)
            for object_summary in bucket.objects.all():
                object_key = object_summary.key
                self.write({
                    's3_uri': f"s3://{self.bucket_name}/{object_key}",
                })
            self.write({'state': "pushed"})
