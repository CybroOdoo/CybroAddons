# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'Barcode For Community',
    'version': "17.0.1.0.0",
    'category': 'Warehouse',
    'summary': 'Custom Inventory Barcode',
    'description': 'Barcode for the Inventory Adjustments and Transfers',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['stock_picking_batch', 'mrp_subcontracting'],
    'data': [
        'reports/custom_barcode_report.xml',
        'reports/custom_barcode_templates.xml',
        'views/stock_location_views.xml',
        'views/stock_picking_type_views.xml',
        'views/res_config_settings_views.xml',
        'views/ir_actions_client_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_picking_batch_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'barcode_for_community/static/src/view/**/*',
            'barcode_for_community/static/src/js/choosePicking.js',
            'barcode_for_community/static/src/xml/choosePicking.xml',
            'barcode_for_community/static/src/js/custom_barcode.js',
            'barcode_for_community/static/src/js/barcode_adjustment.js',
            'barcode_for_community/static/src/js/barcode_adjustment_lines.js',
            'barcode_for_community/static/src/js/barcode_batch.js',
            'barcode_for_community/static/src/js/barcode_location.js',
            'barcode_for_community/static/src/js/barcode_location_lines.js',
            'barcode_for_community/static/src/js/barcode_operation_type.js',
            'barcode_for_community/static/src/js/barcode_dialog.js',
            'barcode_for_community/static/src/lib/quagga.js',
            'barcode_for_community/static/src/xml/barcode_adjustment_templates.xml',
            'barcode_for_community/static/src/xml/barcode_batch_templates.xml',
            'barcode_for_community/static/src/xml/barcode_location_templates.xml',
            'barcode_for_community/static/src/xml/barcode_operation_type_templates.xml',
            'barcode_for_community/static/src/xml/barcode_templates.xml',
            'barcode_for_community/static/src/xml/barcode_dialog.xml',
            'barcode_for_community/static/src/js/barcode_sound_service.js',
            'barcode_for_community/static/src/scss/style.css',
            'barcode_for_community/static/src/scss/custom_barcode.scss',
        ],
        'web.qunit_suite_tests': [
            'barcode_for_community/static/src/tests/*'
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True
}
