# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Oil & Gas Core',
    'version': '19.0.1.0.0',
    'category': 'Oil ERP/Foundation',
    'summary': 'Core configuration, shared models, settings, security groups for Oil ERP',
    'description': """
Foundation module for the Oil & Gas ERP system.
Provides core configuration, custom theme, shared models, and basic security groups.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'base_setup',
        'web',
        'mail',
        'sale',
        'purchase',
        'account',
        'base_accounting_kit',
        'uom',
    ],
    'data': [
        'security/oil_security.xml',
        'security/ir.model.access.csv',
        'views/dashboard_views.xml',
        'views/res_config_settings_views.xml',
        'views/oil_menus.xml',
        'views/oil_reporting_menus.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'oil_erp_base/static/src/scss/primary_variables.scss',
        ],
        'web.assets_backend': [
            'oil_erp_base/static/src/xml/menu_panels.xml',
            'oil_erp_base/static/src/xml/nav_bar_panel.xml',
            'oil_erp_base/static/src/xml/home_menus.xml',
            'oil_erp_base/static/src/xml/side_bar_panel.xml',
            'oil_erp_base/static/src/scss/backend_theme.scss',
            'oil_erp_base/static/src/js/home_menus.js',
            'oil_erp_base/static/src/js/search_apps.js',
            'oil_erp_base/static/src/dashboard/dashboard.js',
            'oil_erp_base/static/src/dashboard/dashboard.xml',
            'oil_erp_base/static/src/dashboard/dashboard.scss',
            'oil_erp_base/static/src/dashboard/operation_dashboard.js',
            'oil_erp_base/static/src/dashboard/operation_dashboard.xml',
            'oil_erp_base/static/src/dashboard/operation_dashboard.scss',
        ],
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
    'post_init_hook': 'post_init_hook',
}
