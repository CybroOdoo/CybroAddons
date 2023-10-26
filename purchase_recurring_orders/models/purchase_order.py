# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ruksana P  (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    """ Purchase order inherited for adding two fields is_agreement and
     recurring_agreement_id """
    _inherit = 'purchase.order'

    is_agreement = fields.Boolean(string='From Agreement?', copy=False,
                                  help="Checking this box represents that "
                                       "purchase order is from agreement.")
    recurring_agreement_id = fields.Many2one('purchase.recurring.agreement',
                                             string='Agreement Reference',
                                             help="This indicates the Purchase"
                                                  " Agreement",
                                             ondelete='restrict')

    @api.model
    def _prepare_agreement_vals(self, order):
        """ Method for creating agreement values"""
        return {
            'partner_id': order.partner_id.id,
            'company_id': order.company_id.id,
            'start_date': fields.Datetime.now(),
        }

    @api.model
    def _prepare_agreement_line_vals(self, order_ids, agreement):
        """ Returns the Agreement Line Values in a Dictionary Format"""
        return {
            'recurring_agreement_id': agreement.id,
            'product_id': order_ids.product_id.id,
            'quantity': order_ids.product_qty,
        }

    def action_generate_agreement(self):
        """Generates Purchase Recurring Agreement"""
        agreements = []
        for purchase_order in self:
            agreement_vals = self._prepare_agreement_vals(purchase_order)
            agreement = self.env[
                'purchase.recurring.agreement'].create(agreement_vals)
            agreements.append(agreement)
            for order_id in purchase_order.order_line:
                agreement_line_vals = self._prepare_agreement_line_vals(
                    order_id, agreement)
                self.env['recurring.agreement.line'].create(agreement_line_vals)
        if len(agreements) == 1:
            view = self.env.ref(
                'purchase_recurring_orders.'
                'purchase_recurring_agreement_view_form')
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'purchase.recurring.agreement',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': agreement[0].id,
                'nodestroy': True,
            }
        return True
