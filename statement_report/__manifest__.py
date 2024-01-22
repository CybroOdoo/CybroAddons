# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
    'name': 'Customer/ Supplier Payment Statement Report',
    'version': '17.0.1.0.0',
    'category': 'Productivity',
    'summary': """Customer/ Supplier Payment Statement Report is designed to 
     manage all customer and/or supplier payment statement reports.""",
    'description': """ This module help you to get Customer/ Supplier
     Payment Statement Report, auto send monthly statement to customer and 
     enables option to share pdf and excel report""",
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
    'auto_install': False,
    'installable': True,
    'application': False
}
