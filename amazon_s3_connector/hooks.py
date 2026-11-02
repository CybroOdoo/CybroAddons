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


def uninstall_hook(env):
    """
    Deletes System Parameters
    """
    env['ir.config_parameter'].sudo().search(
        [('key', 'in', [
            'amazon_s3_connector.amazon_access_key',
            'amazon_s3_connector.amazon_secret_key',
            'amazon_s3_connector.amazon_bucket_name',
            'amazon_s3_connector.amazon_connector',
        ])]).unlink()
