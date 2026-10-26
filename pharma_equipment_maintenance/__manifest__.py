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
    'name': 'Pharmaceutical ERP — Equipment Qualification & Maintenance',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'GMP equipment register with qualification, calibration, '
               'cleaning and QA-verified maintenance.',
    'description': """Tracks equipment qualification, calibration, cleaning and maintenance requests
through QA verification. Manufacturing orders and QC results check equipment
fitness before use.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'pharmaceutical_base',
        'maintenance',
        'mrp',
    ],
    'data': [
        'security/pharma_equipment_security.xml',
        'security/ir.model.access.csv',
        'data/pharma_equipment_data.xml',
        'data/pharma_equipment_cron.xml',
        'views/maintenance_equipment_category_views.xml',
        'wizard/pharma_equipment_requalify_wizard_views.xml',
        'views/pharma_equipment_qualification_views.xml',
        'views/maintenance_equipment_views.xml',
        'views/maintenance_request_views.xml',
        'views/pharma_calibration_result_views.xml',
        'wizard/pharma_equipment_override_wizard_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_workcenter_views.xml',
        'views/pharma_qc_spec_views.xml',
        'views/pharma_qc_test_order_views.xml',
        'views/pharma_value_source_views.xml',
        'views/product_template_views.xml',
        'views/res_config_settings_views.xml',
        'views/menus.xml',
        'views/pharma_reporting_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pharma_equipment_maintenance/static/src/dashboard/equipment_tiles.scss',
            'pharma_equipment_maintenance/static/src/dashboard/equipment_tiles.js',
            'pharma_equipment_maintenance/static/src/dashboard/equipment_tiles.xml',
            'pharma_equipment_maintenance/static/src/request_kanban/request_kanban.js',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
