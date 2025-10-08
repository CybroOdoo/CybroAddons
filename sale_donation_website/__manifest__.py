# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    'name': "Website Sale Donation",
    'description': """To add the donation in the website""",
    'summary': """User can select created donations in the website""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'maintainer': "Cybrosys Techno Solutions",
    'category': 'Sales/Sales',
    'version': '16.0.1.0.0',
    'depends': ['base', 'sale_management', 'website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/product_product_data.xml',
        'views/donation_rule_views.xml',
        'views/donation_lines_views.xml',
        'views/donation_menu.xml',
        'views/website_sale_donation_views.xml',
        'views/sale_order_views.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    'assets': {
        'web.assets_frontend': [
            'sale_donation_website/static/src/js/website_sale_donation.js',
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
