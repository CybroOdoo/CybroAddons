# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fasluca @ cybrosys,(odoo@cybrosys.com)
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
    'name': 'Product Attachments on Website',
    'version': '14.0.1.0.0',
    'summary': """This Module Allows Customer to Download Documents
    That Are Attached to the Products From Website""",
    'description': 'This Module allows customer to download documents '
                   'that are attached to the products from website',
    'category': 'Website',
    'author': 'Frontware, Cybrosys Techno Solutions',
    'company': 'Frontware, Cybrosys Techno Solutions',
    'maintainer': 'Frontware, Cybrosys Techno Solutions',
    'website': "https://github.com/Frontware/CybroAddons",
    'depends': ['website_sale'],
    'data': ['views/template.xml'],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
