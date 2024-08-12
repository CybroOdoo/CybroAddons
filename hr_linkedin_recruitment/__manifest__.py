# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'summary': "Basic module for LnkedIn-HR Recruitment connector",
    'description': """The LinkedIn-HR Recruitment Connector Basic Module is
    designed to optimize your recruitment workflow, offering a comprehensive 
    suite of features to enhance candidate sourcing and selection.""",
    'category': 'Generic Modules/Human Resources',
    'version': "17.0.1.0.0",
    'depends': ['hr_recruitment', 'auth_oauth'],
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'data': [
        'data/auth_linkedin_data.xml',
        'security/ir.model.access.csv',
        'views/recruitment_config_settings.xml',
        'views/hr_job_linkedin_likes_comments_views.xml',
        'views/linkedin_comments_views.xml',
        'views/oauth_views.xml',
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
