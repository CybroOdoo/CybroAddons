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
        self.write({'state': 'draft'})
        return super(SaleOrder, self).action_confirm()

    def _needs_approval(self):
        """ Helper method to check if the sale order needs approval """
        self.ensure_one()
        if not self.company_id.so_double_validation:
            return False

        if not self.env['ir.config_parameter'].sudo().get_param(
                'sales_order_double_approval.so_approval'):
            return False

        min_amount = float(
            self.env['ir.config_parameter'].sudo().get_param(
                'sales_order_double_approval.so_min_amount', default=0))

        if self.amount_total <= min_amount:
            return False

        if self.env.user.has_group('sales_team.group_sale_manager'):
            return False

        return True

    def action_confirm(self):
        """ Override to add double validation logic based on company settings.
        Confirms the sale order if conditions are met, otherwise sets state to
        'to_approve'. """
        if self._needs_approval():
            self.write({'state': 'to_approve'})
            return True

        return super(SaleOrder, self).action_confirm()

    def action_cancel(self):
        """ Method to cancel the sale order and change state into 'cancel' """
        self.write({'state': 'cancel'})
