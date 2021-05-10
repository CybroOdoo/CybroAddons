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
    'name': 'Theme Rozz',
    'description': 'Design Web Pages with Theme Rozz',
    'summary': 'Design Web Pages with Theme Rozz',
    'category': 'Theme/Corporate',
    'version': '14.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website', 'website_crm', 'website_blog'],
    'data': [
            'views/snippets/rozz_banner.xml',
            'views/snippets/rozz_services.xml',
            'views/snippets/rozz_team.xml',
            'views/snippets/rozz_aboutus.xml',
            'views/snippets/about_us.xml',
            'views/snippets/services_page.xml',
            'views/snippets/rozz_subscribe.xml',
            'views/snippets/portfolio_page.xml',
            'views/snippets/portfolio_details.xml',
            'views/contact_us.xml',
            'views/blog_templates.xml',
            'views/header.xml',
            'views/footer.xml',
            'views/assets.xml',
            'views/layout.xml',
    ],
    'images': [
        'static/description/banner.png',
        'static/description/image_screenshot.png',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
