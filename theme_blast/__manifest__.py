# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Theme Blast',
    'version': '14.0.1.0.0',
    'summary': 'Theme Blast',
    'description': 'Theme Blast Front-end theme',
    'category': 'Theme/Corporate',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'license': 'AGPL-3',
    'depends': ['website_sale', 'website_mass_mailing'],
    'data': [
        'data/blasst_configuration_data.xml',
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/blast_configuration_view.xml',
        'views/asked_questions_view.xml',
        'views/partner_testimonial.xml',
        'views/snippets/askedquestions.xml',
        'views/snippets/banner.xml',
        'views/snippets/clients.xml',
        'views/snippets/choose.xml',
        'views/snippets/best_deal.xml',
        'views/snippets/best_products_carousal.xml',
        'views/snippets/cardsnippet.xml',
        'views/snippets/features.xml',
        'views/snippets/sub.xml',
        'views/footer.xml',
        'views/views.xml'

    ],
    'images': [
        'static/description/banner.jpg',
        'static/description/blast_screenshot.jpg',
    ],
    'installable': True,
    'auto_install': False,
}
