# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amaya Aravind(odoo@cybrosys.com)
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
    'name': 'Extra Social Media In Website',
    'version': '16.0.1.0.0',
    'category': 'Website',
    'summary': 'Snippet for adding extra social medias in website.',
    'description': "This provides an option  to add extra social medias "
                   "like YouTube, Google+, Pinterest, Flickr etc. in website"
                   " by using inner content snippet.The social medias that "
                   "have values in the configuration settings will be only "
                   "visible in the website.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website'],
    'data': [
        'views/res_config_setting_views.xml',
        'views/snippets/extra_social_media_templates.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'website_extra_social_media/static/src/js/extra_social_media.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
