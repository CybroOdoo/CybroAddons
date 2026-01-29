# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
################################################################################
{
    'name': 'Invoice Mini Dashboard',
    'version': '15.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Mini dashboard for invoicing module',
    'description': "Module provide a mini dashboard for invoicing modules"
                   " with some use full details such as paid, unpaid, expected"
                   "revenue and state wise count of invoice",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['account'],
    'data': [
        'views/account_move_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'invoice_mini_dashboard/static/src/scss/invoice.scss',
            'invoice_mini_dashboard/static/src/js/invoice_dashboard.js',
            'invoice_mini_dashboard/static/src/js/invoice_bill_dashboard.js',
        ],
        'web.assets_qweb': [
            'invoice_mini_dashboard/static/src/xml/invoice_dashboard.xml',
            'invoice_mini_dashboard/static/src/xml/invoice_bill_dashboard.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
