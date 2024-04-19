# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Vishnu KP(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': 'HR Recruitment Twitter Integration',
    'version': "17.0.1.0.0",
    'category': 'Extra Tools',
    'summary': """Share your job positions directly to twitter.""",
    'description': """This integration module makes your HR recruitment better.
     You can share your Job positions directly to Twitter""",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'depends': ['hr_recruitment', 'website'],
    'data': [
        "views/hr_job_views.xml",
        "views/res_config_settings_views.xml"
    ],
    'external_dependencies': {
        'python': ['tweepy'],
    },
    'assets': {
        'web.assets_backend': [
            'recruitment_twitter/static/src/js/many2many_binary.js']},
    'images': ['static/description/banner.jpg'],
    'license': "AGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False
}
