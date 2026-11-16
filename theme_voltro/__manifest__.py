################################################################################
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
################################################################################
{
    'name': 'Theme Voltro',
    'version': '20.0.1.0.0',
    'category': 'Theme/Corporate',
    'summary': 'Theme Voltro is an advanced eCommerce theme crafted for '
               'digital product marketplaces. It transforms your online '
               'store into a sophisticated, technology-focused platform'
               ' with a sleek dark mode interface and modern design.',
    'description': 'Theme Voltro is an Advanced eCommerce Theme designed specifically'
                   ' for Digital Product Marketplaces. This Theme transforms your '
                   'online store into a sophisticated technology-focused platform '
                   'with its sleek dark mode interface and modern aesthetics.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale'],
    'data': [
        'views/product_template_views.xml',
        'views/snippets/banner.xml',
        'views/snippets/product_categories.xml',
        'views/snippets/offer.xml',
        'views/snippets/arrivals.xml',
        'views/snippets/launches.xml',
        'views/snippets/brands.xml',
        'views/snippets/contact_us.xml',
        'views/snippets/sub_banner.xml',
        'views/snippets/services.xml',
        'views/snippets/about_story.xml',
        'views/snippets/achievements.xml',
        'views/snippets/about_team.xml',
        'views/snippets/snippets.xml',
        'views/header.xml',
        'views/footer.xml',
        'views/home.xml',
        'views/about.xml',
        'data/website_menu_data.xml',
        'views/contact_us.xml',
        'views/product_view_template.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'theme_voltro/static/src/scss/primary_variables.scss',
        ],
        'web.assets_frontend': [
            'theme_voltro/static/lib/gsap/gsap.js',
            'theme_voltro/static/lib/gsap/ScrollTrigger.js',
            'theme_voltro/static/lib/splide/splide.js',
            'theme_voltro/static/lib/splide/splide.css',
            'theme_voltro/static/lib/bootstrap_icons/bootstrap-icons.css',
            'theme_voltro/static/src/css/style.css',
            'theme_voltro/static/src/css/layout.css',
            'theme_voltro/static/src/css/snippets.css',
            'theme_voltro/static/src/css/shop_card.css',
            'theme_voltro/static/src/js/*.js',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
