# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
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
################################################################################
{
    'name': 'Payment Proof Attachment',
    'category': 'Website',
    'version': '16.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'summary': """Proof Attachment In Website for Odoo 16 Community and 
     Enterprise Edition.""",
    'description': """This module allows the customers to attach proof 
    attachments in the website""",
    'images': ['static/description/banner.png'],
    'depends': [
        'base',
        'website_sale',
        'sale_management'
    ],
    'data': [
        'views/template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_proof_attachment/static/src/js/my_account_screen.js',
            'payment_proof_attachment/static/src/js/payment_screen.js',
            'payment_proof_attachment/static/src/css/payment_proof.css',
        ]
    },
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
