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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Advanced HR-LinkedIn Integration',
    'version': "18.0.1.0.0",
    'category': 'Human Resources',
    'summary': "This module for LnkedIn-HR Recruitment connector",
    'description': """The LinkedIn-HR Recruitment Connector Module is
     designed to optimize your recruitment workflow, offering a comprehensive 
     suite of features to enhance candidate sourcing and selection.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['hr_recruitment', 'auth_oauth'],
    'data': [
        'security/ir.model.access.csv',
        'data/auth_oauth_provider_data.xml',
        'views/auth_oauth_provider_views.xml',
        'views/hr_job_views.xml',
        'views/linkedin_comments_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'external_dependencies':
        {
        'python': ['mechanize', 'linkedin'],
        },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
