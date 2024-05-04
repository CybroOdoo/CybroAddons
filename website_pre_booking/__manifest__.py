# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#############################################################################
{
    'name': 'Website Pre Booking',
    'version': '16.0.1.0.0',
    'category': 'Website',
    'summary': 'Allows pre booking option for website',
    'description': """This module will help you to managing prebooking of
     product management in website""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'license': 'AGPL-3',
    'depends': ['portal', 'website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/portal_views.xml',
        'views/website_prebook_views.xml',
        'views/website_sale_inherit.xml',
        'views/prebook_details_template.xml',
        'views/pre_booking_template.xml',
        'views/product_template_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/website_pre_booking/static/src/css/prebooking.css'
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
