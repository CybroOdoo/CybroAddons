# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
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
    'name': 'Website Product Reservation',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': 'Enable product reservation functionality on your website',
    'description': "This module extends the website functionality by enabling "
                   "product reservation. Allow your customers to reserve "
                   "products directly from your website, and manage these "
                   "reservations seamlessly within the Odoo environment. "
                   "Enhance the shopping experience by providing a reservation"
                   " feature for in-demand products.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale', 'stock'],
    'data': [
        'data/website_menu.xml',
        'views/product_template_views.xml',
        'views/res_cofig_settings_views.xml',
        'views/sale_order_views.xml',
        'views/website_templates.xml',
        'views/portal_templates.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
