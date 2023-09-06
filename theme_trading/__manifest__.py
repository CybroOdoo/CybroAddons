# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vivek @ cybrosys,(odoo@cybrosys.com)
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
    'name': 'Theme Trading',
    'version': '14.0.1.0.0',
    'category': 'Theme/Corporate',
    'summary': 'Theme Trading for Odoo Trading Website',
    'description': """
    Theme Trading is an attractive trading Website theme which comes with many 
    useful and stylish snippets
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png',
    ],
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'website_blog', 'website_form'],
    'data': [
        'views/assets.xml',
        'views/trading_templates.xml',
        'views/investing_templates.xml',
        'views/footer.xml',
        'views/header.xml',
        'views/website_menus.xml',
        'views/contactus.xml',
        'views/snippets/feature_templates.xml',
        'views/snippets/community_templates.xml',
        'views/snippets/asset_classes_templates.xml',
        'views/snippets/banner_templates.xml',
        'views/snippets/aboutus_templates.xml',
        'views/snippets/faq_templates.xml',
        'views/snippets/testimonial_templates.xml',
        'views/snippets/snippet_templates.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
