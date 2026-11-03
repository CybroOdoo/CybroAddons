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
    'name': 'BOM Comparison Report',
    'version': '20.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Compare the component prices of the bills of materials of a product in a PDF report.',
    'description': """
     Compare the bills of materials of a product in a PDF report. Select two
     or more bills of materials, the number of products to produce and the
     analysis method, cost or sales price of the components, and get the
     price of the components of each bill of materials for one product and
     for the products to produce, with the most profitable one highlighted.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['mrp'],
    'data': [
        'security/ir.access.csv',
        'wizard/bom_comparison_views.xml',
        'views/mrp_bom_views.xml',
        'reports/bom_comparison_template.xml',
        'reports/ir_actions_report.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            'bom_comparison_report/static/src/scss/bom_comparison_report.scss',
        ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
