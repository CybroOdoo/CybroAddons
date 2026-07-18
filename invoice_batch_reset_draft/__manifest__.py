# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Posted Invoices to Draft in Bulk',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Reset (or cancel) multiple posted invoices, bills and refunds '
               'from the list view in one action.',
    'description': """
Posted Invoices to Draft in Bulk
================================
Select several invoices/bills/credit notes in the list view and, from the
Action menu, reset the posted ones to Draft in one click (reusing Odoo's
standard reset-to-draft logic). Ineligible records (locked/hashed periods,
tax cash-basis entries, records needing a cancellation request, etc.) are
automatically skipped and reported, so one bad record never blocks the batch.

Features
--------
* Bulk "Reset to Draft" and "Cancel" actions on the invoice/bill list view.
* Graceful per-record processing with a skip-and-summarise report.
* Optional Reason, logged in each affected invoice's chatter (audit trail).
* Restricted to the Accounting Manager group.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base_accounting_kit'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/batch_reset_draft_wizard_views.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
