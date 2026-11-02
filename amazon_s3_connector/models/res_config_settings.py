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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """
    Configure the access credentials
    """
    _inherit = 'res.config.settings'

    amazon_access_key = fields.Char(
        string='Amazon S3 Access Key',
        config_parameter='amazon_s3_connector.amazon_access_key',
        help='Enter your Amazon S3 Access Key here.')
    amazon_secret_key = fields.Char(
        string='Amazon S3 Secret Key',
        config_parameter='amazon_s3_connector.amazon_secret_key',
        help='Enter your Amazon S3 Secret Key here.')
    amazon_bucket_name = fields.Char(
        string='Amazon S3 Bucket Name',
        config_parameter='amazon_s3_connector.amazon_bucket_name',
        help='Enter the name of your Amazon S3 Bucket here.')
    is_amazon_connector = fields.Boolean(
        config_parameter='amazon_s3_connector.amazon_connector',
        default=False,
        help='Enable or disable the Amazon S3 connector.')
