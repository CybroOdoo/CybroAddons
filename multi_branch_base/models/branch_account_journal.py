# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields, api


class AccountJournal(models.Model):
    """inherited account journal"""
    _inherit = "account.journal"

    def _get_branch_domain(self):
        """methode to get branch domain"""
        company = self.env.company
        branch_ids = self.env.user.branch_ids
        branch = branch_ids.filtered(
            lambda branch: branch.company_id == company)
        return [('id', 'in', branch.ids)]

    branch_id = fields.Many2one('res.branch', string='Branch',
                                domain=_get_branch_domain,
                                help='Leave this field empty if this journal is'
                                     ' shared between all branches')

    default_account_id = fields.Many2one(
        comodel_name='account.account', check_company=True, copy=False,
        ondelete='restrict',
        string='Default Account',
        domain="[('deprecated', '=', False), ('company_id', '=', company_id),"
               "'|', ('user_type_id', '=', default_account_type), "
               "('user_type_id', 'in', type_control_ids),"
               "('user_type_id.type', 'not in', ('receivable', 'payable')),"
               "'|',('branch_id', '=', branch_id), ('branch_id', '=', False)]")

    suspense_account_id = fields.Many2one(
        comodel_name='account.account', check_company=True, ondelete='restrict',
        readonly=False, store=True,
        compute='_compute_suspense_account_id',
        help="Bank statements transactions will be posted on the suspense "
             "account until the final reconciliation "
             "allowing finding the right account.", string='Suspense Account',
        domain=lambda self: "[('deprecated', '=', False), "
                            "('company_id', '=', company_id), \
                            ('user_type_id.type', 'not in', "
                            "('receivable', 'payable')), \
                            ('user_type_id', '=', %s), '|',"
                            "('branch_id', '=', branch_id), "
                            "('branch_id', '=', False)]" % self.env.ref(
                             'account.data_account_type_current_liabilities').id)

    profit_account_id = fields.Many2one(
        comodel_name='account.account', check_company=True,
        help="Used to register a profit when the ending balance of a cash "
             "register differs from what the system computes",
        string='Profit Account',
        domain=lambda self: "[('deprecated', '=', False), "
                            "('company_id', '=', company_id), \
                            ('user_type_id.type', 'not in', "
                            "('receivable', 'payable')), \
                            ('user_type_id', 'in', %s),"
                            "'|', ('branch_id', '=', branch_id), "
                            "('branch_id', '=', False)]" % [
                             self.env.ref(
                                 'account.data_account_type_revenue').id,
                             self.env.ref(
                                 'account.data_account_type_other_income').id])

    loss_account_id = fields.Many2one(
        comodel_name='account.account', check_company=True,
        help="Used to register a loss when the ending balance of a cash "
             "register differs from what the system computes",
        string='Loss Account',
        domain=lambda self: "[('deprecated', '=', False), "
                            "('company_id', '=', company_id), \
                                 ('user_type_id.type', 'not in', "
                            "('receivable', 'payable')), \
                                 ('user_type_id', '=', %s), '|', "
                            "('branch_id', '=', branch_id), "
                            "('branch_id', '=', False)]" % self.env.ref(
                             'account.data_account_type_expenses').id)

    @api.onchange('branch_id')
    def onchange_branch_id(self):
        """onchange methode"""
        self.default_account_id = False
        self.suspense_account_id = False
        self.profit_account_id = False
        self.loss_account_id = False
