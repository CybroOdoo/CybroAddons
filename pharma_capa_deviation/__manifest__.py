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
    'name': 'Pharmaceutical ERP — CAPA & Deviations',
    'version': '20.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Quality Deviation and Corrective & Preventive Action (CAPA) '
               'management for the Pharmaceutical ERP suite.',
    'description': """Deviations classified by phase, severity and root cause, raised from
     BMR steps, IPQC results and QC test orders, with linked Corrective and
     Preventive Actions tracked from Open to Closed.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'pharmaceutical_base',
    ],
    'data': [
        'security/ir.access.csv',
        'data/pharma_sequences_data.xml',
        'data/pharma_premium_feature_data.xml',
        'views/pharma_capa_views.xml',
        'views/pharma_deviation_views.xml',
        'views/pharma_qc_test_order_views.xml',
        'views/pharma_ipqc_result_views.xml',
        'views/pharma_bmr_views.xml',
        'views/res_config_settings_views.xml',
        'views/menus.xml',
        'views/pharma_reporting_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
