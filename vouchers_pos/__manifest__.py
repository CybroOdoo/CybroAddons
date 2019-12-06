# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Cybrosys Technologies(<https://www.cybrosys.com>)

#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################
{
    'name': 'Coupons & Vouchers in Point of Sale',
    'version': '13.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Manage Point of Sale Vouchers & Coupon Codes',
    'author': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'depends': ['point_of_sale'],
    'data': [
             'data/product_data.xml',
             'views/gift_voucher.xml',
             'views/applied_coupons.xml',
             'views/pos_template.xml',
             'security/ir.model.access.csv'
            ],
    'qweb': ['static/src/xml/coupons.xml'],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
