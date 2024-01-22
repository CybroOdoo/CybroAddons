# -*- coding: utf-8 -*-
###############################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Subina P (odoo@cybrosys.com)
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
from odoo import SUPERUSER_ID, api


def uninstall_hook(cr):
    """
    Deletes System Parameters
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['ir.config_parameter'].sudo().search(
        [('key', '=', 'dropbox_integration.client_id')]).unlink()
    env['ir.config_parameter'].sudo().search(
        [('key', '=', 'dropbox_integration.client_secret')]).unlink()
    env['ir.config_parameter'].sudo().search(
        [('key', '=', 'dropbox_integration.folder_id')]).unlink()
    env['ir.config_parameter'].sudo().search(
        [('key', '=', 'dropbox_integration.dropbox_button')]).unlink()
