# -*- coding: utf-8 -*-
###############################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Aslam A K( odoo@cybrosys.com )
#
#   You can modify it under the terms of the GNU AFFERO
#   GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#   You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#   (AGPL v3) along with this program.
#   If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, SUPERUSER_ID


def uninstall_hook(cr, registry):
    """ Deletes System Parameters on uninstalling application """
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['ir.config_parameter'].sudo().search(
        [('key', '=', 'amazon_s3_connector.amazon_access_key')]).unlink()
    env['ir.config_parameter'].sudo().search(
        [('key', '=', 'amazon_s3_connector.amazon_secret_key')]).unlink()
    env['ir.config_parameter'].sudo().search(
        [('key', '=', 'amazon_s3_connector.amazon_bucket_name')]).unlink()
    env['ir.config_parameter'].sudo().search(
        [('key', '=', 'amazon_s3_connector.amazon_button')]).unlink()
