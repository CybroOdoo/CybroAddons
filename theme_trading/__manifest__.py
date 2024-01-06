# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swathy K S (odoo@cybrosys.com)
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
##############################################################################
{
    'name': 'Theme Trading',
    'version': '17.0.1.0.0',
    'category': 'Theme/Corporate',
    'summary': 'Theme Trading is an attractive trading Website theme. '
               'The theme comes with many useful and stylish snippets',
    'description': 'Theme Trading for Odoo Trading Website',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website'],
    'data': [
        'views/theme_trading_templates.xml',
        'views/theme_trading_investing_templates.xml',
        'views/footer_templates.xml',
        'views/header_templates.xml',
        'views/website_views.xml',
        'views/contactus_templates.xml',
        'views/snippets/theme_trading_feature_templates.xml',
        'views/snippets/theme_trading_community_templates.xml',
        'views/snippets/theme_trading_asset_classes_templates.xml',
        'views/snippets/theme_trading_banner_templates.xml',
        'views/snippets/theme_trading_aboutus_templates.xml',
        'views/snippets/theme_trading_faq_templates.xml',
        'views/snippets/theme_trading_testimonial_templates.xml',
        'views/snippets/snippet_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            "theme_trading/static/src/css/style.css",
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,

}
