# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Pharmaceutical ERP',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Make medicines and manage their quality, all in one place.',
    'description': """Core pharmaceutical manufacturing and quality management.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'mail',
        'mrp',
        'purchase',
        'stock',
        'purchase_stock',
        'account',
        'hr',
        'base_setup',
        'website',
        'product_expiry'
    ],
    'sequence': 50,
    'data': [
        'security/pharma_groups.xml',
        'security/ir.model.access.csv',
        'data/pharma_sequences_data.xml',
        'views/product_template_views.xml',
        'views/pharma_qc_spec_line_views.xml',
        'views/pharma_qc_spec_views.xml',
        'views/mrp_bom_views.xml',
        'views/stock_move_line_views.xml',
        'views/stock_lot_views.xml',
        'views/pharma_bmr_step_views.xml',
        'views/pharma_ipqc_result_views.xml',
        'views/pharma_bmr_views.xml',
        'views/mrp_production_views.xml',
        'views/pharma_qc_result_line_views.xml',
        'views/pharma_qc_test_order_views.xml',
        'views/pharma_oos_investigation_views.xml',
        'views/purchase_order_views.xml',
        'views/res_config_settings_views.xml',
        'views/pharma_menus.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'pharmaceutical_base/static/src/scss/primary_variables.scss',
        ],
        'web.assets_backend': [
            'pharmaceutical_base/static/src/scss/backend_theme.scss',
            'pharmaceutical_base/static/src/css/pharma_bmr.css',
            'pharmaceutical_base/static/src/components/dashboard/dashboard.scss',
            'pharmaceutical_base/static/src/components/dashboard/dashboard.js',
            'pharmaceutical_base/static/src/components/dashboard/dashboard.xml',
            'pharmaceutical_base/static/src/js/sidebar.js',
            'pharmaceutical_base/static/src/js/search_apps.js',
            'pharmaceutical_base/static/src/js/home_menus.js',
            'pharmaceutical_base/static/src/scss/sidebar.scss',
            'pharmaceutical_base/static/src/xml/side_bar_panel.xml',
            'pharmaceutical_base/static/src/xml/menu_panels.xml',
            'pharmaceutical_base/static/src/xml/home_menus.xml',
        ],
        'web.assets_web_dark': [
            'pharmaceutical_base/static/src/scss/backend_theme.dark.scss',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
