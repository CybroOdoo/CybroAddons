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
    'name': "Odoo Amazon S3 Connector",
    'version': '20.0.1.0.0',
    'category': 'Document Management',
    'summary': """Browse and upload Amazon S3 files from Odoo""",
    'description': """Browse, search and download the files of an Amazon
                      S3 bucket from a dashboard in Odoo, and upload new
                      files to it.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base_setup'],
    'data': [
        'security/ir.access.csv',
        'views/amazon_dashboard_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/amazon_upload_file_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'amazon_s3_connector/static/src/scss/amazon.scss',
            'amazon_s3_connector/static/src/js/amazon.js',
            'amazon_s3_connector/static/src/xml/amazon_dashboard_template.xml',
        ],
    },
    'external_dependencies': {'python': ['boto3']},
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
    'uninstall_hook': 'uninstall_hook',
}
