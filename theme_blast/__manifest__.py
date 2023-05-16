# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Theme Blast',
    'version': '16.0.1.0.0',
    'summary': 'Theme Blast',
    'description': 'Theme Blast Front-end theme',
    'category': 'Theme/Corporate',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale', 'website_mass_mailing'],
    'data': [
        'data/blast_configuration_data.xml',
        'security/ir.model.access.csv',
        'views/blast_configuration_views.xml',
        'views/asked_questions_views.xml',
        'views/res_partner_views.xml',
        'views/snippets/website_snippets_inherit.xml',
        'views/snippets/askedquestions.xml',
        'views/snippets/banner.xml',
        'views/snippets/clients.xml',
        'views/snippets/choose.xml',
        'views/snippets/best_deal.xml',
        'views/snippets/best_products_carousal.xml',
        'views/snippets/cardsnippet.xml',
        'views/snippets/features.xml',
        'views/snippets/sub.xml',
        'views/views.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_blast/static/src/css/owl.carousel.min.css',
            'theme_blast/static/src/css/owl.theme.default.min.css',
            'theme_blast/static/src/scss/_variables.scss',
            'theme_blast/static/src/scss/_normalize.scss',
            'theme_blast/static/src/scss/_common.scss',
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
            'theme_blast/static/src/js/snippets/best_deal/000.js',
            'theme_blast/static/src/js/snippets/best_products_carousel/000.js',
            'theme_blast/static/src/js/snippets/testimonial/testimonial.js',
            'theme_blast/static/src/js/owl.carousel.min.js',
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
