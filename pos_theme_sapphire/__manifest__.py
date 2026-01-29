# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: THASNI CP (odoo@cybrosys.com)
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
    'name': 'POS Theme Sapphire',
    'version': '15.0.1.0.0',
    'category': 'Themes/Backend',
    'summary': """Minimalist and elegant backend POS theme for Odoo 15""",
    'description': 'The POS Theme Sapphire Is A Responsive And Ultimate Theme For Your Odoo V15.'
                   'This Theme Will Give You A New Experience With Odoo.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
    'depends': ['base', 'point_of_sale'],
    'assets': {
        'point_of_sale.assets': [
            'pos_theme_sapphire/static/src/css/custom.css',
        ],
        'web.assets_qweb': [
            'pos_theme_sapphire/static/src/xml/**/CashierName.xml',
            'pos_theme_sapphire/static/src/xml/**/CashMoveButton.xml',
            'pos_theme_sapphire/static/src/xml/**/HeaderButton.xml',
            'pos_theme_sapphire/static/src/xml/**/TicketButton.xml',
            'pos_theme_sapphire/static/src/xml/**/CategoryButton.xml',
            'pos_theme_sapphire/static/src/xml/**/ProductItem.xml',
            'pos_theme_sapphire/static/src/xml/**/ProductScreen.xml',
            'pos_theme_sapphire/static/src/xml/**/ProductsWidget.xml',
            'pos_theme_sapphire/static/src/xml/**/ProductsWidgetControlPanel.xml',
            'pos_theme_sapphire/static/src/xml/Chrome.xml',
        ],
    },
}
