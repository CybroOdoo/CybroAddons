# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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
    'version': '19.0.1.0.0',
    'category': 'Website',
    'summary': """Enable customers to upload proof attachments directly through the website.""",
    'description': """This module provides functionality for customers to submit proof attachments via the website 
    interface. Uploaded files are securely stored and linked to the relevant records, supporting streamlined 
    validation and processing workflows. The feature integrates seamlessly with the existing website flow, 
    ensuring a consistent user experience and efficient document management.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'website_sale',
        'sale_management'
    ],
    'data': [
        'views/sale_templates.xml',
        'data/mail_template_data.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_proof_attachment/static/src/js/*.js',
            'payment_proof_attachment/static/src/css/payment_proof.css',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
