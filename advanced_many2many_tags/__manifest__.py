# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swetha Anand (odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Advanced Many2many Tags',
    'version': '15.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Copy the text and open the form view of Many2many tags.',
    'description': """
    This module helps to open the record and to copy the text of Many2many tags 
    in Odoo. New dialog box is added to choose the option on clicking the tag.
    This feature added to the many2many_tags widget.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.jpg'],
    'depends': ['base', 'web'],
    'assets': {
        'web.assets_backend': {
            'advanced_many2many_tags/static/src/js/many2many_tags_field.js'
        }
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
