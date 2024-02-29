# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
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
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
{
	'name': 'POS All in One Report Generator',
	'version': '17.0.1.0.0',
	'category': 'Point of Sale',
	'summary': "Dynamic Point Of Sale Report Maker",
	'description': """Dynamic Point Of Sale Report Maker Which generates report
	 based on On Orders, Order Details, Product, Categories, Salesman and
	 Payment""",
	'author': 'Cybrosys Techno Solutions',
	'company': 'Cybrosys Techno Solutions',
	'maintainer': 'Cybrosys Techno Solutions',
	'website': 'https://www.cybrosys.com',
	'depends': ['point_of_sale', 'stock', 'web'],
	'data': [
		'security/ir.model.access.csv',
		'report/pos_order_report_templates.xml',
		'views/pos_report_menus.xml',
	],
	'assets': {
		'web.assets_backend': [
			'pos_report_generator/static/src/js/PosReport.js',
			'pos_report_generator/static/src/xml/PosReport.xml',
			'pos_report_generator/static/src/css/pos_report.css',
		],
	},
	'images': ['static/description/banner.png'],
	'license': 'AGPL-3',
	'installable': True,
	'auto_install': False,
	'auto_install': False,
}
