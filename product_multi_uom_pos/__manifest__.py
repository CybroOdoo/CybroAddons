# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: LINTO C T(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'POS Product Multiple UOM',
    'version': '14.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Multiple UOM for Products',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale', 'stock'],
    'data': [
             'views/pos_template.xml',
             'views/pos_view_extended.xml',
            ],
    'qweb': ['static/src/xml/pos.xml'],
    'images': ['static/description/banner.png',
		'static/description/icon.png'],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
