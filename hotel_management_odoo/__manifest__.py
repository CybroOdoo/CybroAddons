# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Hotel Management',
    'version': '15.0.1.0.1',
    'summary': 'Hotel Management Application for odoo 15',
    'description': """The module helps you to manage rooms,amenities,services,restaurants.
                      End Users can book rooms and reserve foods from hotel restaurant.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'category': 'Sales',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'account', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/room_reservation.xml',
        'views/hotel_meals.xml',
        'views/hotel_restaurant.xml',
        'views/res_settings.xml',
        'views/hotel_amenity.xml',
        'views/hotel_services.xml',
        'views/room_checkin_in_out.xml',
        'views/menus.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
