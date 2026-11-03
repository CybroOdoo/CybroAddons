#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': "POS Product Magnify Image",
    'version': '20.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """Magnify product images in POS""",
    'description': "Allows you to enlarge the image of every product in the "
                   "POS with a button click.",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_magnify_image/static/src/css/pos_magnify_image.css',
            'pos_magnify_image/static/src/js/MagnifyProductPopup.js',
            'pos_magnify_image/static/src/xml/MagnifyProductPopup.xml',
            'pos_magnify_image/static/src/js/product_magnify_image.js',
            'pos_magnify_image/static/src/xml/product_magnify_image.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
