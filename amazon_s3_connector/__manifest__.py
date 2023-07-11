# -*- coding: utf-8 -*-
###############################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Aslam A K( odoo@cybrosys.com )
#
#   You can modify it under the terms of the GNU AFFERO
#   GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#   You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#   (AGPL v3) along with this program.
#   If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': "Odoo Amazon S3 Connector",
    'version': "16.0.1.0.0'",
    'category': "Document Management",
    'summary': """ Connect with Amazon S3 Files from Odoo""",
    'description': """This module was developed to upload to Amazon S3 Cloud 
                      Storage as well as access files from Amazon S3 Cloud 
                      Storage in Odoo.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'images': ['static/description/banner.png'],
    'depends': ['base_setup'],
    'data': [
        'security/ir.model.access.csv',
        'views/amazon_dashboard_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/amazon_upload_file_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'amazon_s3_connector/static/src/js/amazon.js',
            'amazon_s3_connector/static/src/xml/amazon_dashboard_template.xml',
            'amazon_s3_connector/static/src/scss/amazon.scss'
        ]
    },
    'license': 'AGPL-3',
    'external_dependencies': {'python': ['boto3']},
    'application': True,
    'installable': True,
    'auto_install': False,
    'uninstall_hook': 'uninstall_hook'
}
