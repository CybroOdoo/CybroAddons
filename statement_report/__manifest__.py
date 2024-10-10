# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Customer/ Supplier Payment Statement Report',
    'version': '18.0.1.0.0',
    'category': 'Productivity',
    'summary': """This module is designed to generate  Customer/Supplier Payment
    Statement Reports.""",
    'description': """This module helps to generate Customer/Supplier Payment
    Statement Reports, automatically send monthly statements to customers, and
    provides the option to share Pdf and Excel reports.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'account', 'contacts'],
    'data': [
        'data/ir_cron_data.xml',
        'views/res_partner_views.xml',
        'report/res_partner_reports.xml',
        'report/res_partner_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/statement_report/static/src/js/action_manager.js',
        ]
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
