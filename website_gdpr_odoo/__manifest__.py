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
    'name': 'Website GDPR In Odoo',
    'version': '20.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Website',
    'summary': """Website GDPR, GDPR Compliance, Personal Data, Data Download, Data Deletion, Customer Portal, Privacy, Odoo20 Website, Odoo20 Portal""",
    'description': """
        Customers open the Personal Data page of their portal and request a
        download or the deletion of the personal data listed in a GDPR
        template. The website administrator approves or cancels each request;
        an approved download gives the customer a PDF of their data, and an
        approved deletion clears the selected fields of the contact. The
        customer is informed by email.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'portal', 'contacts'],
    'data': [
        'security/ir.access.csv',
        'data/ir_sequence_data.xml',
        'data/portal_entry_data.xml',
        'data/mail_template_data.xml',
        'views/gdpr_request_views.xml',
        'views/gdpr_template_views.xml',
        'views/gdpr_portal_templates.xml',
        'report/gdpr_request_reports.xml',
        'report/gdpr_request_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_gdpr_odoo/static/src/js/gdpr_portal.js',
            'website_gdpr_odoo/static/src/scss/gdpr_portal.scss',
        ],
        'web.assets_tests': [
            'website_gdpr_odoo/static/tests/tours/*.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
