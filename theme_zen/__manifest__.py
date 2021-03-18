# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Theme Zen',
    'description': 'Design Web Pages with theme zen',
    'summary': 'Theme Zen',
    'category': 'Theme/Corporate',
    'version': '14.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'website'],
    'data': [
        'views/index/index_banner.xml',
        'views/index/index_about.xml',
        'views/index/index_testinomial.xml',
        'views/index/index_blog.xml',
        'views/index/index_partners.xml',
        'views/index/index_recent.xml',
        'views/index/index_video.xml',
        'views/about/about.xml',
        'views/service/service.xml',
        'views/portfolio/portfolio.xml',
        'views/contact/contact.xml',
        'views/blog/blog.xml',
        'views/assets.xml',
        'views/templates.xml',
    ],
    'images': [
        'static/description/banner.png',
        'static/description/zen_screenshot.png',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
