# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2018-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Tintuk Tomin(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU AGPL (v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AGPL (AGPL v3) for more details.
#
##############################################################################

{
    'name': 'Product Volume Calculation',
    'version': '12.0.1.0.0',
    'summary': """This module will helps you to give dimensions of the product.""",
    'description': "Module helps you to manage the length, breadth and height of the product and calculates its volume accordingily.",
    'category': "Inventory",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base','stock'],
    'data': [
             'views/volume_view.xml'
             ],
    'demo': [],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
}
