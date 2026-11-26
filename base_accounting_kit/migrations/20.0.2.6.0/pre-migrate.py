# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
"""The common report wizard form moved out of a no-update block.

``account_report_view_form`` was in the ``noupdate`` block of
``data/account_financial_report_data.xml``; it is now in the normal view file
``wizard/account_common_report_views.xml``. Odoo still skips records whose
external ID is flagged ``noupdate``, so clear the flag before the module is
loaded: this upgrade (and the next ones) update the view.
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        UPDATE ir_model_data
           SET noupdate = FALSE
         WHERE module = 'base_accounting_kit'
           AND name = 'account_report_view_form'
    """)
