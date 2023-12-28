# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """This class inherits the model 'res.config.settings' and adds
     required fields"""
    _inherit = 'res.config.settings'

    def _get_account_manager_ids(self):
        """This function  gets all the records of 'res.users'  and
        it filters the 'res.users' records to select only those users
        who belong to the 'account.group_account_manager' group."""
        user_ids = self.env['res.users'].search([])
        account_manager_ids = user_ids.filtered(
            lambda x: x.has_group('account.group_account_manager'))
        return [('id', 'in', account_manager_ids.ids)]
    payment_approval = fields.Boolean(string='Payment Approval',
                                      config_parameter='account_payment_'
                                                       'approval.payment_'
                                                       'approval',
                                      help="Enable/disable payment"
                                           " approval to approve for payment "
                                           "if needed.")
    approval_user_id = fields.Many2one('res.users',
                                       string="Payment Approving person",
                                       required=False,
                                       domain=_get_account_manager_ids,
                                       config_parameter='account_payment_'
                                                        'approval.approval_'
                                                        'user_id',
                                       help="Select the payment approving "
                                            "person.")
    approval_amount = fields.Float(
        string='Minimum Approval Amount',
        config_parameter='account_payment_approval.approval_amount',
        help="If amount is 0.00, All the payments go through approval.")
    approval_currency_id = fields.Many2one('res.currency',
                                           string='Approval Currency',
                                           config_parameter='account_payment_'
                                                            'approval.approval_'
                                                            'currency_id',
                                           help="Converts the payment amount"
                                                " to this currency if chosen.")
