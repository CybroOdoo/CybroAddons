# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Product Bidding In ECommerce',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': 'App To Add Bidding option In Website',
    'description': 'Website Bargain is an application where users can create '
                   'and manage bargains on their website, enabling their '
                   'customers to participate in bidding and negotiate prices '
                   'for products or services',
    'author': 'Cybrosys Techno Solution',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solution',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
        'views/website_bargain_views.xml',
        'views/bargain_template_views.xml',
        'views/bargain_information_views.xml',
        'views/bargain_subscribers_views.xml',
        'views/product_template_views.xml',
        'views/website_shop_auction_templates.xml',
        'views/website_product_views_templates.xml',
        'views/website_bargain_menus.xml',
        'views/bidders_information_templates.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'website_bargain/static/src/js/website_bargain.js',
            'website_bargain/static/src/css/website_product_bargain.css',
        ]},
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto-install': False,
    'application': False,
}
