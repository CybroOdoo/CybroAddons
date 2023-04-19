# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies @cybrosys(odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'HR Recruitment Twitter Integration',
    'depends': ['base', 'hr_recruitment', 'website'],
    'version': "15.0.1.0.0",
    'summary': """ Share your Job positions directly to Twitter.""",
    'description': """This integration module makes your HR recruitment better.
                       You can share your Job positions directly to Twitter""",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'category': 'Tools',
    'images': ['static/description/banner.png'],
    'data': [
        "views/hr_job.xml",
        "views/res_config_settings.xml"
    ],
    'external_dependencies': {
        'python': ['tweepy'],
    },
    'license': "AGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False
}
