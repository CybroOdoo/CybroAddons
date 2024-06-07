# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anagha S (odoo@cybrosys.com)
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
###############################################################################
{
    'name': "Machine Repair Barcode Scanner",
    'version': '16.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Barcode Scanner in Repair Orders',
    'description': """This module helps to generates EAN13 standard barcode for 
     Product and create a repair order by scanning the barcode.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base_machine_repair_management'],
    'data': [
        'views/machine_repair_views.xml',
        'views/product_product_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'machine_repair_barcode_scanner/static/src/js/'
            'machine_barcode_scan.js',
            'machine_repair_barcode_scanner/static/src/js/quagga.js',
            'machine_repair_barcode_scanner/static/src/css/styles.css',
            'machine_repair_barcode_scanner/static/src/xml/'
            'machine_repair_barcode_templates.xml',
        ],
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
