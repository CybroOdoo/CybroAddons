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
{
    'name': 'Minimal Backend Theme',
    'version': '20.0.1.0.0',
    'category': 'Theme/Backend',
    'summary': 'Calm backend theme: search menus and records, pins, app board, sidebar, dark mode, mobile and RTL',
    'description': """
A calm, focused backend theme for Odoo 20 (plum for actions, teal for links,
Odoo's own fonts and font sizes):

* Global search (top bar, Ctrl+Shift+F): menus of all apps and records
  (contacts, orders, leads, invoices...), quick create ("new lead"),
  pinned menus and recently opened records.
* Full-screen app board with pinned shortcuts.
* Menus in the top bar or in a collapsible sidebar (a drawer on tablets).
* Dark mode, compact view and full-width forms, from Quick settings in the
  top bar or Settings > General Settings > Backend Theme (shared by all
  users, changed by administrators).
* Responsive on phones and tablets; right-to-left languages supported.

See static/description/index.html for the full description.
""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'license': 'LGPL-3',
    'images': ['static/description/banner.gif'],
    'depends': ['web', 'base_setup'],
    'data': [
        'security/ir.access.csv',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            (
                'before',
                'web/static/src/scss/primary_variables.scss',
                'minimal_backend_theme/static/src/scss/primary_variables.scss',
            ),
        ],
        'web.assets_backend': [
            'minimal_backend_theme/static/src/scss/theme.scss',
            'minimal_backend_theme/static/src/menu_search/*',
            'minimal_backend_theme/static/src/theme_settings.js',
            'minimal_backend_theme/static/src/personal/*',
            'minimal_backend_theme/static/src/menu_layout/sidebar.*',
            'minimal_backend_theme/static/src/quick_settings/*',
            'minimal_backend_theme/static/src/full_width_forms/*',
            'minimal_backend_theme/static/src/app_board/*',
        ],
        # Dark palette, loaded ahead of the theme's light variables so its
        # plain assignments win over every !default below.
        'web.assets_web_dark': [
            (
                'before',
                'minimal_backend_theme/static/src/scss/primary_variables.scss',
                'minimal_backend_theme/static/src/scss/primary_variables.dark.scss',
            ),
        ],
        # Lazy-loaded views (pivot, graph) compile in their own bundle, with
        # its own dark variant.
        'web.assets_backend_lazy_dark': [
            (
                'before',
                'minimal_backend_theme/static/src/scss/primary_variables.scss',
                'minimal_backend_theme/static/src/scss/primary_variables.dark.scss',
            ),
        ],
    },
    'installable': True,
    'application': False,
}
