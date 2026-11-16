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
    'name': 'Docusign Odoo Connector',
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': 'Seamless integration between DocuSign and Odoo for electronic signatures',
    'description': """This module integrates DocuSign with Odoo, allowing users to send sales orders and documents to recipients for electronic signature and automatically retrieve signed documents.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'sale_management', 'mail'],
    'data': [
        'security/ir.access.csv',
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        'views/docusign_credentials_views.xml',
        'views/res_config_settings_views.xml',
        'views/docusign_document_request_views.xml',
        'views/sale_order_views.xml',
        'views/res_partner_views.xml',
        'wizard/send_document_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'docusign_odoo_connector/static/src/js/edit_document.js',
            'docusign_odoo_connector/static/src/xml/pdf_viewer_field.xml',
            'docusign_odoo_connector/static/src/js/docusign_many2many_binary.js',
            'docusign_odoo_connector/static/src/xml/docusign_many2many_binary.xml',
        ],
    },
    'external_dependencies': {
        'python': ['docusign-esign']
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
