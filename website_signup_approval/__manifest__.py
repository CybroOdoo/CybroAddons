# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': "Website Signup Approval",
    'version': '16.0.1.0.0',
    'summary': 'Approve signup request to login to the website',
    'description': """This module approve or reject signup approval request of 
     users from website.User can upload their documents for approval.""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'category': 'Website',
    'depends': ['website', 'sale_management', 'web'],
    'data': [
        'security/website_signup_approval_groups.xml',
        'security/ir.model.access.csv',
        'data/mail_channel_data.xml',
        'views/res_users_approve_views.xml',
        'views/res_config_settings_views.xml',
        'views/signup_templates.xml',
        'views/document_attachment_views.xml',
        'views/approval_request_templates.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'website_signup_approval/static/src/js/signup.js'
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
