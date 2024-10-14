# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Muhsina V (<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'Social Media Icon Styles in Website',
    'version': '16.0.1.0.0',
    'category': 'Website',
    'summary': "Customized style for website social media sharing buttons",
    'description': "This module helps to share the product on social media "
                   "like Facebook, Twitter, LinkedIn, WhatsApp, email, "
                   "Pinterest, Reddit or Hacker News, Also provide 10+ styles "
                   "for social media sharing button. User can enable/disable "
                   "these social media platforms from the settings.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/share_social_media_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_social_media_icon_style/static/src/scss/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
