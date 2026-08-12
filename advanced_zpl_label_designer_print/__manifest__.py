# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    'name': 'ZPL Label Designer',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Interactive ZPL Label Designer for Odoo',
    'description': """
        Design ZPL labels using an interactive drag-and-drop designer.
        - Support for text, barcodes, and images.
        - Custom label sizes and DPI settings.
        - Real-time ZPL generation.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'web', 'product','stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/label_paper_formats.xml',
        'views/zpl_label_template_views.xml',
        'views/zpl_label_element_views.xml',
        'views/report_zpl_template.xml',
        'views/product_label_layout_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js',
            'advanced_zpl_label_designer_print/static/src/js/designer_canvas.js',
            'advanced_zpl_label_designer_print/static/src/js/designer_widget.js',
            'advanced_zpl_label_designer_print/static/src/xml/designer_templates.xml',

        ],
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,

    'auto_install': False,
}
