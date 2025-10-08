# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jaseem (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
{
    'name': "Barcode for work centers",
    'version': '16.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Start and stop the work ordr using barcode',
    'description': """This module enables the functionality to initiate and 
     halt work orders using barcode scanning. It allows users to commence work 
     orders by scanning barcodes and provides buttons to pause and resume work 
     order activities.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ["stock_barcode", "stock", "mrp"],
    'data': [
        "data/barcode_for_work_centers.xml",
        "views/mrp_routing_workcenter_views.xml",
    ],
    'assets': {
        'web.assets_backend': [
            '/barcode_for_work_centers/static/src/js/barcode_template.js',
            '/barcode_for_work_centers/static/src/xml/manufacture_button_templates.xml',
            '/barcode_for_work_centers/static/src/xml/barcode_scan_templates.xml',
            '/barcode_for_work_centers/static/src/css/barcode_for_work_centers.scss',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'OPL-1',
    'installable': True,
    'application': False,
    'auto_install': False,
}

