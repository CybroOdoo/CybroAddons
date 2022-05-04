# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aswani pc @ cybrosys(odoo@cybrosys.com)
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
    'name': "Pos Order Line Product Image",
    'version': '14.0.1.0.0',
    'summary': """Product image in pos order lines""",
    'description': """This module adds product image in pos order lines, Odoo14, Odoo 14""",
    'author': "Frontware, Cybrosys Techno Solutions",
    'company': "Frontware, Cybrosys Techno Solutions",
    'website': "https://github.com/Frontware/CybroAddons",
    'category': 'Point of Sale',
    'depends': ['point_of_sale'],
    'data': ['views/pos_order_line_image.xml'],
    'qweb': ['static/src/xml/pos_order_line.xml'],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
}
