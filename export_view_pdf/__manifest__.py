# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': "Export View PDF",
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Export Current List View in PDF Format""",
    'description': """This module will add option to export the details of the 
     current list vie in the PDF format.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base','web'],
    'data':
        [
            'data/export_paper_format.xml',
            'report/export_pdf_group_by_template.xml',
            'report/export_pdf_template.xml',
            'report/ir_exports_report.xml',
        ],
    'assets': {
        'web.assets_backend': [
            'export_view_pdf/static/src/js/export_dialog.js',
            'export_view_pdf/static/src/js/pdf_export.js',
            'export_view_pdf/static/src/xml/export_dialog.xml',
            'export_view_pdf/static/src/xml/export_pdf_dropdown.xml'
        ]
    },
    'images': [
        'static/description/banner.jpg'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
