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
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError


# The five Odoo 20 lock dates (core res.company), in screen order.
LOCK_FIELDS = ('fiscalyear_lock_date', 'tax_lock_date', 'sale_lock_date',
               'purchase_lock_date', 'hard_lock_date')


class AccountUpdateLockDate(models.TransientModel):
    """Accounting > Closing > Lock Dates: sets the five core lock dates of
    the company. Core ``res.company._validate_locks`` checks them (the Hard
    Lock Date cannot move back; draft entries / unreconciled bank lines
    block a lock)."""
    _name = 'account.lock.date'
    _description = 'Lock date for accounting'

    company_id = fields.Many2one(comodel_name='res.company', string="Company",
                                 required=True)
    fiscalyear_lock_date = fields.Date(
        string="Global Lock Date",
        help="No entry up to and including this date, except for users "
             "with a lock exception.")
    tax_lock_date = fields.Date(
        string="Tax Return Lock Date",
        help="No entry with taxes up to and including this date (set it "
             "once the tax return is filed).")
    sale_lock_date = fields.Date(
        string="Sales Lock Date",
        help="No customer invoice or credit note up to and including this "
             "date.")
    purchase_lock_date = fields.Date(
        string="Purchase Lock Date",
        help="No vendor bill or refund up to and including this date.")
    hard_lock_date = fields.Date(
        string="Hard Lock Date",
        help="Final: no entry up to and including this date, for everyone, "
             "without exceptions. It can only move forward.")

    @api.model
    def default_get(self, field_list):
        res = super().default_get(field_list)
        company = self.env.company
        res['company_id'] = company.id
        res.update({field: company[field] for field in LOCK_FIELDS})
        return res

    def _check_execute_allowed(self):
        self.ensure_one()
        # Chief Accountant (implied by Administrator), as the Lock Dates menu.
        allowed = self.env.user.has_group('base_accounting_kit.group_account_chief')
        if not (allowed or self.env.uid == SUPERUSER_ID):
            raise UserError(_("You are not allowed to execute this action."))

    def execute(self):
        self.ensure_one()
        self._check_execute_allowed()
        company = self.company_id.sudo()
        # Only the dates that change: core checks each written lock date.
        values = {field: self[field] for field in LOCK_FIELDS
                  if self[field] != company[field]}
        if values:
            company.write(values)
        return {'type': 'ir.actions.act_window_close'}
