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
    'name': 'Pharmaceutical ERP — Retention Samples',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Reserve (retention) sample register for released batches: '
               'withdrawals, periodic examination and approved disposal.',
    'description': """Retention sample register for the Pharmaceutical ERP suite.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'pharmaceutical_base',
        'pharma_traceability_coa',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/pharma_retention_data.xml',
        'views/stock_location_views.xml',
        'views/pharma_retention_withdrawal_views.xml',
        'views/pharma_retention_sample_views.xml',
        'wizard/pharma_retention_disposal_wizard_views.xml',
        'views/product_template_views.xml',
        'views/stock_lot_views.xml',
        'views/pharma_qa_release_views.xml',
        'views/res_config_settings_views.xml',
        'views/menus.xml',
        'views/pharma_reporting_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
