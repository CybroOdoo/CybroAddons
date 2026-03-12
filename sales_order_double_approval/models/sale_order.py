# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
from odoo import fields, models


class SaleOrder(models.Model):
    """ Inheriting sale.order to add new state """
    _inherit = 'sale.order'

    state = fields.Selection(selection_add=
                             [('to_approve', 'To Approve'),
                              ('sent',)], ondelete={'to_approve': 'cascade'})

    def button_approve(self):
        """ Method to approve the sale order and change its state to 'sale' """
        self.write({'state': 'sale'})

    def action_confirm(self):
        """ Override to add double validation logic based on company settings.
        Confirms the sale order if conditions are met, otherwise sets state to
        'to_approve'. """
        res = super(SaleOrder, self).action_confirm()
        if self.company_id.so_double_validation:
            if self.env['ir.config_parameter'].sudo().get_param(
                    'sales_order_double_approval.so_approval'):
                if self.amount_total > float(
                        self.env['ir.config_parameter'].sudo().get_param(
                            'sales_order_double_approval.so_min_amount')):
                    if self.env.user.has_group('sales_team.group_sale_manager'):
                        self.state = 'sale'
                    else:
                        self.state = 'to_approve'
        return res

    def action_cancel(self):
        """ Method to cancel the sale order and change state into 'cancel' """
        self.state = 'cancel'
