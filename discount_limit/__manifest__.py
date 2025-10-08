# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev K P (odoo@cybrosys.com)
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
################################################################################
{
	'name': "POS Discount Limit & Restrict Global Discount",
	'version': '16.0.1.0.0',
	'category': 'Point of Sale',
	'summary': """This module is used to limit the discount on pos 
	product category.""",
	'description': """This module is used to limit the discount on pos
	 product category and also restrict the global discount for selected cashiers.""",
	'author': "Cybrosys Techno Solutions",
	'company': 'Cybrosys Techno Solutions',
	'maintainer': 'Cybrosys Techno Solutions',
	'website': "https://www.cybrosys.com",
	'depends': ['web', 'pos_hr', 'pos_discount'],
	'data': [
		'views/res_config_settings_views.xml',
		'views/product_template_views.xml',
		'views/pos_category_views.xml',
		'views/hr_employee_views.xml',
	],
	'assets': {
        'web.assets_backend': [
            'discount_limit/static/src/js/Orderline.js',
            'discount_limit/static/src/js/PosGlobalState.js',
            'discount_limit/static/src/js/DiscountButton.js',
        ],
    },
	'images': ['static/description/banner.png'],
	'license': 'AGPL-3',
	'installable': True,
	'auto_install': False,
	'application': False,
}
