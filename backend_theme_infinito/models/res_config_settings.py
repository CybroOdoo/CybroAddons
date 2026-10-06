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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """
   Model representing configuration settings for the system.
   This model allows the administrator to configure various settings
   related to the user interface and system behavior.
   """

    _inherit = 'res.config.settings'

    is_user_edit = fields.Boolean('User edit', default=False, config_parameter='backend_theme_infinito.is_user_edit')
    is_sidebar_enabled = fields.Boolean('Sidebar Enabled', default=False, config_parameter='backend_theme_infinito.is_sidebar_enabled')
    is_fullscreen_enabled = fields.Boolean('Full screen Enabled', default=False, config_parameter='backend_theme_infinito.is_fullscreen_enabled')
    is_sidebar_icon = fields.Boolean('Sidebar icon Enabled', default=True, config_parameter='backend_theme_infinito.is_sidebar_icon')
    is_sidebar_name = fields.Boolean('Sidebar name Enabled', default=True, config_parameter='backend_theme_infinito.is_sidebar_name')
    is_sidebar_company = fields.Boolean('Sidebar Company Enabled',
                                        default=True, config_parameter='backend_theme_infinito.is_sidebar_company')
    is_sidebar_user = fields.Boolean('Sidebar User Enabled', default=True, config_parameter='backend_theme_infinito.is_sidebar_user')
    is_recent_apps = fields.Boolean('Recent Apps Enabled', default=False, config_parameter='backend_theme_infinito.is_recent_apps')
    is_fullscreen_app = fields.Boolean('Full screen Apps Enabled',
                                       default=False, config_parameter='backend_theme_infinito.is_fullscreen_app')
    is_rtl = fields.Boolean('Rtl Enabled', default=False, config_parameter='backend_theme_infinito.is_rtl')
    is_dark = fields.Boolean('Dark mode Enabled', default=False, config_parameter='backend_theme_infinito.is_dark')
    is_menu_bookmark = fields.Boolean('Menu Bookmark mode Enabled',
                                      default=False, config_parameter='backend_theme_infinito.is_menu_bookmark')
    is_chameleon = fields.Boolean('Chameleon mode Enabled', default=False, config_parameter='backend_theme_infinito.is_chameleon')
    dark_mode = fields.Selection([
        ('all', 'All'),
        ('schedule', 'Schedule'),
        ('auto', 'Automatic'),
    ], default='all', config_parameter='backend_theme_infinito.dark_mode')
    dark_start = fields.Float('Dark Start', default=19.0, config_parameter='backend_theme_infinito.dark_start')
    dark_end = fields.Float('Dark End', default=5.0, config_parameter='backend_theme_infinito.dark_end')
    loader_class = fields.Char('Loader', default='default', config_parameter='backend_theme_infinito.loader_class')

