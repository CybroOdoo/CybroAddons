# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Shahil MP @cybrosys(odoo@cybrosys.com)
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
    'name': 'Import Product From Excel',
    'summary': 'Import Product From Excel or CSV File, Import Product Image From URL and Path',
    'version': '13.0.1.0.0',
    'description': """Import product from excel,XLSX,CSV,Import product image from Excel,Import product from URL,
		      Import product from path,import product details usinf xlsx,import product,odoo13 sales,odoo13,
		      odoo13 xlsx,odoo13,mport product barcode from csv,Import product price from csv,Import product type from csv,
		      create product from csv,Import product from csv""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'category': 'Sales',
    'license': 'AGPL-3',
    'images': ['static/description/banner.png'],
    'depends': ['sale_management', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_url.xml',
        'wizard/product_import.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
