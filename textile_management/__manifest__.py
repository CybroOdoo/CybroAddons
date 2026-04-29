# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Prathyunnan R(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
######################################################################################
{
    'name': 'Textile Management',
    'version': '18.0.1.0.0',
    'category': 'Extra Tools',
    'summary': "To manage Textile Industry",
    'description': """To manage textile industry process such as purchase of 
    raw materials, manufacture the product and sale the final product""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'purchase', 'stock', 'mail', 'mrp',
                'website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_data.xml',
        'views/inquiry_form_success_templates.xml',
        'views/customer_feedback_templates.xml',
        'views/textile_management_menus.xml',
        'views/website_inquiry_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_bom_views.xml',
        'views/textile_management_templates.xml',
        'views/product_template_views.xml',
        'report/textile_report.xml',
        'report/textile_report_templates.xml',
        'wizard/textile_report_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'textile_management/static/src/js/review_and_rating.js',
            'textile_management/static/src/css/review_and_rating.css'
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': True,
    'post_init_hook': 'post_init_hook',
}
