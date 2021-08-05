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
    'name': 'Theme Splash',
    'description': 'Design Web Pages with Theme Splash',
    'summary': 'Design Web Pages with Theme Splash',
    'category': 'Theme/Corporate',
    'version': '14.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'website', 'website_blog'],
    'data': ['views/assets.xml',
             'views/footer.xml',
             'views/header.xml',
             'views/contact_us.xml',
             'views/views.xml',
             'views/blog.xml',
             'views/blog_details.xml',
             'views/snippets/about.xml',
             'views/snippets/service.xml',
             'views/snippets/index/index_banner.xml',
             'views/snippets/index/index_about.xml',
             'views/snippets/index/index_tab_section.xml',
             'views/snippets/index/index_about_section.xml',
             'views/snippets/index/index_service.xml',
             'views/snippets/index/index_expect_tab.xml',
             'views/snippets/index/index_commercial_service.xml',
             'views/snippets/index/index_testmonial.xml',
             'views/snippets/index/index_blog.xml',
             'views/snippets/index/index_partner.xml'
             ],
    'images': [
        'static/description/banner.png',
        'static/description/splash_screenshot.png'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
