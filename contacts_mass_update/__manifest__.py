# -- coding: utf-8 --
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Contacts Mass Update',
    'version': '18.0.1.0.0',
    'category': 'Sale',
    'summary': 'Modify some fields of multiple partners',
    'sequence': 10,
    'description': """
        Contacts Mass Update
        ====================
        * 2-Step Wizard: 1) Select partners, 2) Modification form
        * Select Multiple partners: Based on filters or manual selection(Server action)
        * Filters: Country, State, Partner type(Customers, Vendors, Both, All)
        * Access ways: Menu Item and Server action in contacts module
        * Fields: Salesperson, Pricelist, Tags, Payment terms,
        Payment methods, Fiscal position, Company.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'contacts', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/contacts_mass_update_action.xml',
        'wizard/contacts_mass_update_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
