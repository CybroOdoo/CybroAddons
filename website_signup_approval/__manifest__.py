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
    'name': "Website Signup Approval",
    'version': '20.0.1.0.0',
    'category': 'Website',
    'summary': 'Approve website signup requests for user login',
    'description': """This module allows administrators to approve or
reject signup requests of users from the website. Users can upload
required documents for approval during registration.""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['auth_signup', 'website', 'sale', 'website_sale'],
    'data': [
        'security/website_signup_approval_groups.xml',
        'security/ir.access.csv',
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
