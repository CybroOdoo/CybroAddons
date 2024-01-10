# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Renjith (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'OCR Data Retrieval',
    'version': '15.0.1.0.0',
    'category': 'Productivity',
    'summary': """Data retrieval from scanned documents with .jpg, .jpeg, .png 
     and .pdf file format""",
    'description': """OCR data retrieval from scanned documents is the process 
     of extracting machine-readable text and potentially other relevant 
     information from physical or digital images of documents.""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'hr_expense', 'bill_digitization', 'contacts',
                'purchase', 'sale_management'],
    'assets': {
        'web.assets_backend': [
            '/ocr_data_retrieval/static/src/js/image_field.js',
        ],
    },
    'data': ['security/ir.model.access.csv',
             'views/ocr_data_template_views.xml'],
    'external_dependencies': {
        'python': ['pdf2image', 'PIL', 'pytesseract', 'spacy',
                   'en_core_web_sm']
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
