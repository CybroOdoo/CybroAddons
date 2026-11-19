# -*- coding: utf-8 -*-
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
    """ Delete system parameters when the module is uninstalled. """
    keys = [
        'dropbox_integration.client_id',
        'dropbox_integration.client_secret',
        'dropbox_integration.folder_id',
        'dropbox_integration.dropbox_button',
    ]
    env['ir.config_parameter'].sudo().search([('key', 'in', keys)]).unlink()
