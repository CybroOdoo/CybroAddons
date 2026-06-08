# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

{
    'name': 'Account Report Send By Mail',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'summary': "Create account report based on user requirements and send it "
               "by mail",
    'description': "This app enables users to generate personalized "
                   "account reports based on their email address. Users have "
                   "the flexibility to choose the type of report they want, "
                   "catering to their specific needs. After selecting the "
                   "desired report type, users can input the recipients email "
                   "address to seamlessly send the generated report.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['account', 'account_reports'],
    'data': [
        'security/ir.model.access.csv',
        'data/account_report_mail_template.xml',
        'wizard/send_mail_report_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'account_report_send_by_mail/static/src/css/send_mail_report.css',
            'account_report_send_by_mail/static/src/js/report_action.js',
            'account_report_send_by_mail/static/src/xml/report_action.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
