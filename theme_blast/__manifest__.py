# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright(C) 2024-TODAY Cybrosys Techno Solutions
#    (<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Theme Blast',
    'version': '17.0.1.0.0',
    'category': 'Theme/Corporate',
    'summary': 'Theme Blast  makes the website more unique and attractive'
               ' through its style and custom-designed snippet',
    'description': 'Theme Blast Front-end theme provides Structural snippets'
                   ' like Features, Subscribe, Choose , Cards, Banner and'
                   ' Dynamic content snippets ',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['web', 'website_sale', 'website_mass_mailing'],
    'data': [
        'data/blast_configuration_data.xml',
        'security/ir.model.access.csv',
        'views/blast_configuration_views.xml',
        'views/asked_questions_views.xml',
        'views/res_partner_views.xml',
        'views/snippets/snippets_templates.xml',
        'views/snippets/asked_questions_templates.xml',
        'views/snippets/banner_templates.xml',
        'views/snippets/testimonial_templates.xml',
        'views/snippets/choose_templates.xml',
        'views/snippets/best_deal_templates.xml',
        'views/snippets/best_products_carousal_templates.xml',
        'views/snippets/cards_templates.xml',
        'views/snippets/features_templates.xml',
        'views/snippets/subscribe_templates.xml',
        'views/theme_blast_templates.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'https://code.jquery.com/jquery-3.1.0.js',
            'theme_blast/static/src/css/owl.carousel.min.css',
            'theme_blast/static/src/css/style.css',
            'theme_blast/static/src/css/owl.theme.default.min.css',
            'theme_blast/static/src/scss/_variables.scss',
            'theme_blast/static/src/scss/_normalize.scss',
            'theme_blast/static/src/css/owl.carousel.min.css',
            'theme_blast/static/src/scss/components/_buttons.scss',
            'theme_blast/static/src/scss/layout/_navigation.scss',
            'theme_blast/static/src/scss/layout/_banner.scss',
            'theme_blast/static/src/scss/layout/_product.scss',
            'theme_blast/static/src/scss/layout/_footer.scss',
            'theme_blast/static/src/scss/pages/home/_about.scss',
            'theme_blast/static/src/scss/pages/home/_feature.scss',
            'theme_blast/static/src/scss/pages/home/_deal.scss',
            'theme_blast/static/src/scss/pages/home/_choose.scss',
            'theme_blast/static/src/scss/pages/home/_testimonial.scss',
            'theme_blast/static/src/scss/pages/home/_subscribe.scss',
            'theme_blast/static/src/scss/pages/home/_faq.scss',
            'theme_blast/static/src/js/snippets/best_deal/best_deal.js',
            'theme_blast/static/src/js/snippets/best_products_carousel/best_products_carousal.js',
            'theme_blast/static/src/js/snippets/testimonial/testimonial.js',
            'theme_blast/static/src/js/owl.carousel.min.js',
            'theme_blast/static/src/js/scroll.js',
            'theme_blast/static/src/js/snippets/subscribe/subscribe.js',
            'theme_blast/static/src/js/snippets/asked_questions/asked_questions.js',
        ]
    },
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
