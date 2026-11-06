# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Pharmaceutical ERP — Vendor Qualification',
    'version': '20.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Vendor qualification, Approved Vendor List (AVL) and '
               'purchase-order AVL enforcement for the Pharmaceutical ERP suite.',
    'description': """Vendor qualification with an online portal questionnaire and audit
     scoring, an Approved Vendor List per product, and purchase orders blocked
     for vendors outside that list.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'pharmaceutical_base',
        'purchase',
        'stock',
        'mrp',
        'website',
    ],
    'data': [
        'security/ir.access.csv',
        'data/pharma_vq_sequence.xml',
        'data/mail_template_data.xml',
        'views/pharma_avl_views.xml',
        'views/pharma_vendor_qualification_response_views.xml',
        'views/pharma_vendor_qualification_views.xml',
        'views/pharma_questionnaire_question_views.xml',
        'views/pharma_questionnaire_views.xml',
        'views/pharma_portal_templates.xml',
        'views/purchase_order_views.xml',
        'views/pharma_stock_picking_views.xml',
        'views/product_template_views.xml',
        'views/mrp_bom_views.xml',
        'views/menus.xml',
        'views/pharma_reporting_views.xml',
        'wizard/pharma_vendor_qualification_confirm_wizard_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'assets': {
        'web.assets_frontend': [
            'pharma_vendor_qualification/static/src/css/vendor_questionnaire.css',
            'pharma_vendor_qualification/static/src/js/vendor_questionnaire.js',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
