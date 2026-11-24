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
    'name': 'Theme Arqora',
    'version': '20.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': 'An architectural lighting studio theme: a dimmable hero '
               'room, drawing-sheet sections and a refined catalogue.',
    'description': 'Theme Arqora gives a lighting brand a complete website: '
                   'a transparent header over a hero room that the visitor '
                   'lights with the mouse, sections labelled like drawing '
                   'sheets, collections that switch on, a mosaic of signature '
                   'products, light levels by space, an exploded technical '
                   'drawing, projects, services, materials, resources, '
                   'an about page and a contact form. The shop, product page, '
                   'cart and checkout stay the standard eCommerce of Odoo, '
                   'dressed in the same design.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale', 'website_crm'],
    'data': [
        'views/snippets/s_arqora_hero.xml',
        'views/snippets/s_arqora_intro.xml',
        'views/snippets/s_arqora_collections.xml',
        'views/snippets/s_arqora_signature.xml',
        'views/snippets/s_arqora_spaces.xml',
        'views/snippets/s_arqora_projects.xml',
        'views/snippets/s_arqora_craft.xml',
        'views/snippets/s_arqora_journal.xml',
        'views/snippets/s_arqora_page_hero.xml',
        'views/snippets/s_arqora_manifesto.xml',
        'views/snippets/s_arqora_split.xml',
        'views/snippets/s_arqora_services.xml',
        'views/snippets/s_arqora_steps.xml',
        'views/snippets/s_arqora_faq.xml',
        'views/snippets/s_arqora_team.xml',
        'views/snippets/s_arqora_showrooms.xml',
        'views/snippets/s_arqora_materials.xml',
        'views/snippets/s_arqora_resources.xml',
        'views/snippets/snippets.xml',
        'views/layout_templates.xml',
        'views/header_templates.xml',
        'views/dynamic_templates.xml',
        'views/home_templates.xml',
        'views/about_templates.xml',
        'views/services_templates.xml',
        'views/projects_templates.xml',
        'views/materials_templates.xml',
        'views/resources_templates.xml',
        'views/legal_templates.xml',
        'views/contact_templates.xml',
        'views/product_template_views.xml',
        'views/shop_templates.xml',
        'data/website_menu_data.xml',
    ],
    'demo': [
        'demo/shop_demo.xml',
        'demo/product_document_demo.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'theme_arqora/static/src/scss/primary_variables.scss',
        ],
        'web.assets_frontend': [
            'theme_arqora/static/src/scss/fonts.scss',
            'theme_arqora/static/src/scss/arqora.scss',
            'theme_arqora/static/src/scss/header.scss',
            'theme_arqora/static/src/scss/pages.scss',
            'theme_arqora/static/src/scss/shop.scss',
            'theme_arqora/static/src/scss/responsive.scss',
            'theme_arqora/static/src/js/arqora_interactions.js',
        ],
        'website.assets_inside_builder_iframe': [
            'theme_arqora/static/src/scss/edit_mode.edit.scss',
        ],
        'html_builder.iframe_add_dialog': [
            'theme_arqora/static/src/scss/edit_mode.edit.scss',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
