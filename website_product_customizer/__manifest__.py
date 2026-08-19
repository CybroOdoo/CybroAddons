# -- coding: utf-8 --
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Website Product Customizer',
    'version': '18.0.1.0.0',
    'category': 'Website,eCommerce,Sales,Extra Tools',
    'summary': 'Product customization designer for eCommerce',
    'description': """
Website Product Customizer
==========================
A comprehensive product customization module that allows customers to design
and personalize products directly from the eCommerce storefront using a
Fabric.js-powered canvas designer.

Features:
---------
* **Fabric.js Canvas Designer**: Interactive canvas with drag-and-drop, zoom, and real-time preview
* **Text Customization**: Add text objects with font selection, color, size, bold/italic/underline, alignment
* **Image Upload**: Customers upload logos/photos with drag positioning and server-side validation
* **Font Management**: Configurable font library with Google Fonts, system fonts, and custom uploads
* **Color Palettes**: Curated background and text color options per product
* **Design Area Configuration**: Define front and back printable areas with percentage-based boundaries
* **Two-Sided Design**: Front/back toggle for business cards, t-shirts, and similar products
* **Design Templates**: Pre-built templates customers can select and customize
* **Save & Resume**: Customers can save designs as drafts and resume editing later
* **Undo / Redo**: Full state history for all design changes
* **Admin Template Management**: Internal users can save and update reusable templates from the designer
* **Order Integration**: Customization data flows through to sale orders for production
* **Product Categories**: Uses native Odoo eCommerce categories for browsing designable products
* **Demo Data**: Complete demo products across multiple categories
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'website_sale',
        'sale',
        'product',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/product_design_customization_security.xml',

        'data/ir_sequence_data.xml',
        'data/product_public_category_data.xml',
        'data/product_design_template_tag_data.xml',
        'data/product_design_font_data.xml',
        'data/product_design_color_data.xml',

        'views/product_design_template_views.xml',
        'views/product_design_font_views.xml',
        'views/product_design_color_views.xml',
        'views/product_design_customization_views.xml',
        'views/product_template_views.xml',
        'views/product_product_views.xml',
        'views/sale_order_views.xml',
        'views/res_config_settings_views.xml',
        'views/website_product_customizer_menu_views.xml',

        'views/templates.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_product_customizer/static/lib/fabric/fabric.min.js',
            'website_product_customizer/static/src/scss/designer.scss',
            'website_product_customizer/static/src/js/designer.js',
            'website_product_customizer/static/src/js/product_page_button.js',
        ],
        'web.assets_backend': [
            'website_product_customizer/static/src/scss/backend.scss',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
