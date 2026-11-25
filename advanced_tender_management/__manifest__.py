# -*- coding: utf-8 -*-
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
    'name': 'Advanced Tender Management',
    'version': '20.0.1.0.0',
    'category': 'Purchases',
    'summary': 'Create tenders, collect vendor bids on the website and turn '
               'the best bid into a purchase order.',
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mail', 'portal', 'product', 'purchase', 'website'],
    'external_dependencies': {'python': ['openpyxl', 'xlsxwriter']},
    'data': [
        'security/security.xml',
        'security/ir.access.csv',
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        'data/portal_entry_data.xml',
        'views/tender_management_views.xml',
        'views/tender_bidding_views.xml',
        'views/tender_bidding_product_lines_views.xml',
        'views/tender_category_views.xml',
        'views/tender_document_views.xml',
        'views/res_partner_views.xml',
        'views/product_product_views.xml',
        'views/tender_details_templates.xml',
        'views/tender_management_website_templates.xml',
        'views/vendor_management_website_templates.xml',
        'views/tender_snippet_templates.xml',
        'views/res_config_settings_views.xml',
        'views/tender_portal_templates.xml',
        'wizard/import_tender_views.xml',
        'wizard/bid_selection_views.xml',
        'report/tender_bidding_report.xml',
        'report/tender_management_report.xml',
        'views/website_menu_views.xml',
        'views/tender_menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'advanced_tender_management/static/src/js/dashboard.js',
            'advanced_tender_management/static/src/xml/dashboard.xml',
            'advanced_tender_management/static/src/css/dashboard.css',
        ],
        'web.assets_frontend': [
            'advanced_tender_management/static/src/js/snippet.js',
            'advanced_tender_management/static/src/js/tender_bidding.js',
            'advanced_tender_management/static/src/xml/tender_management_templates.xml',
            'advanced_tender_management/static/src/css/tender_snippet_card.css',
            'advanced_tender_management/static/src/css/vendor_registration_form.css',
            'advanced_tender_management/static/src/css/tender_details.css',
        ],
        'web.assets_tests': [
            'advanced_tender_management/static/tests/tours/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
