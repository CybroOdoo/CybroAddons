# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Author: Nilmar Shereef (<shereef@cybrosys.in>)
#    Copyright (C) 2019-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
{
    'name': 'HR-LinkedIn Integration',
    'summary': "Integrates LinkedIn with HR Recruitment",
    'description': "Basic module for LnkedIn-HR Recruitment connector",
    'category': 'Generic Modules/Human Resources',
    'version': "12.0.1.0.0",
    'depends': ['hr_recruitment', 'auth_oauth'],
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'data': [
        'data/auth_linkedin_data.xml',
        'views/recruitment_config_settings.xml',
        'views/hr_job_linkedin.xml',
        'views/oauth_view.xml',
    ],
    'external_dependencies':
        {
        'python': ['mechanize', 'linkedin'],
        },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
