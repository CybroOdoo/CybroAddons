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
from odoo import _, api, fields, models


class AccountLockException(models.Model):
    """Core lock date exceptions (``account.lock_exception``), shown and
    created from Accounting > Closing > Lock Exceptions. Core keeps the
    logic: the exception lowers one soft lock date for one user (or
    everyone) until its end, Revoke ends it, the company chatter logs it."""
    _inherit = 'account.lock_exception'

    kit_company_lock_date = fields.Date(
        string="Current Lock Date",
        compute='_compute_kit_company_lock_date',
        help="The company's lock date that the exception lowers.")

    def _compute_display_name(self):
        super()._compute_display_name()
        for exception in self.filtered(lambda e: not e.id):
            exception.display_name = _("New Lock Exception")

    def action_kit_create(self):
        """Create button of the form: the record is saved by the client
        before the call (users may create exceptions, not edit them, so
        the form has no Save button)."""
        return True

    @api.depends('lock_date_field', 'company_id', 'company_lock_date')
    def _compute_kit_company_lock_date(self):
        for exception in self:
            exception.kit_company_lock_date = exception.company_lock_date \
                if exception.id else (exception.lock_date_field and
                                      exception.company_id[exception.lock_date_field])
