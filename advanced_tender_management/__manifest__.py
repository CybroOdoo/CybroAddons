# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
###############################################################################
{
    'name': "Advanced Tender Management",
    'version': '17.0.1.0.0',
    'category': 'Purchases',
    'summary': 'This module will help you in managing tenders and bids.',
    'description': "This module streamlines the tender management process, allowing "
                   "users to create tenders directly in the system. Vendors can "
                   "submit their bids through the website, and the best tender can be "
                   "selected based on criteria. Once a tender is chosen, a purchase "
                   "order can be generated and sent to the vendor.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'product', 'website', 'purchase', ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
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
        'views/portal_templates.xml',
        'views/tender_portal_templates.xml',
        'views/website_menu_views.xml',
        'views/tender_menu_views.xml',
        'report/tender_bidding_report.xml',
        'report/tender_management_report.xml',
        'wizard/import_tender_views.xml',
        'wizard/bid_selection_views.xml',
    ],
    'assets': {
        "web.chartjs_lib": [
            '/web/static/lib/Chart/Chart.js',
            '/web/static/lib/chartjs-adapter-luxon/chartjs-adapter-luxon.js',
        ],
        'web.assets_backend': [
            'advanced_tender_management/static/src/js/export_template.js',
            'advanced_tender_management/static/src/js/dashboard.js',
            'advanced_tender_management/static/src/xml/dashboard.xml',
            'advanced_tender_management/static/src/css/dashboard.css',
        ],
        'web.assets_frontend': [
            'advanced_tender_management/static/src/js/snippet.js',
            'advanced_tender_management/static/src/js/categories.js',
            'advanced_tender_management/static/src/js/tender_bidding.js',
            'advanced_tender_management/static/src/xml/tender_management_templates.xml',
            'advanced_tender_management/static/src/css/tender_snippet_card.css',
            'advanced_tender_management/static/src/css/vendor_registration_form.css',
            'advanced_tender_management/static/src/css/tender_details.css',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
