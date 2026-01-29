# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Shonima(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': "Many2Many Attachment Preview",
    'version': '15.0.1.0.0',
    'summary': """Preview the attachment in Many2Many field""",
    'description': """"This module helps you to preview the attachments in
     Many2Many fields.""",
    'category': 'Uncategorized',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "http://www.cybrosys.com",
    'depends': ['base', 'sale_management'],
    'data': ['views/sale_order_views.xml'],
    'assets': {
        'web.assets_backend': [
            'many2many_attachment_preview/static/src/js/attachment_preview.js',
        ],
        'web.assets_qweb': [
            'many2many_attachment_preview/static/src/xml/attachment_preview.xml',
        ],
    },
    'license': 'AGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
