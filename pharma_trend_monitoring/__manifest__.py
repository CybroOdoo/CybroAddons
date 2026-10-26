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
    'name': 'Pharmaceutical ERP — Trend Monitoring (OOT)',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Flags QC results outside the normal range QA approved for a '
               'watched parameter, with a trend chart.',
    'description': """Flags QC results outside the QA-approved normal range of a watched parameter
and holds the batch until QA reviews them, with a trend chart and an APQR
trending XLSX export.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'pharmaceutical_base',
    ],
    'external_dependencies': {'python': ['xlsxwriter']},
    'data': [
        'security/pharma_trend_security.xml',
        'security/ir.model.access.csv',
        'report/pharma_trend_report.xml',
        'views/pharma_trend_parameter_views.xml',
        'views/pharma_qc_spec_views.xml',
        'views/pharma_qc_test_order_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/pharma_trend_apqr_export_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pharma_trend_monitoring/static/src/control_chart/control_chart.scss',
            'pharma_trend_monitoring/static/src/control_chart/control_chart.js',
            'pharma_trend_monitoring/static/src/control_chart/control_chart.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
