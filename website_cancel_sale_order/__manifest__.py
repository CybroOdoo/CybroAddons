# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
##############################################################################
{
    'name': "Website Cancel Order",
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': " This app allows you to cancel the sale order by specifying "
               " the reason from website.",
    'description': " This application provides users with the convenience of "
                   " canceling their sale orders directly through the website."
                   " By incorporating a user-friendly interface, it enables"
                   " customers to easily navigate and find the necessary "
                   " options to cancel their orders. ",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale', 'sale_management'],
    'data': [
        'views/sale_portal_templates.xml',
        'views/sale_order_views.xml'],
    'assets': {
        'web.assets_frontend': [
            'website_cancel_sale_order/static/src/js/sale_order_portal.js'],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
