# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ayana KP (odoo@cybrosys.com)
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
    """purchase Order Inherited"""
    _inherit = 'purchase.order'

    @api.model
    def _prepare_agreement_vals(self, order):
        """ Method for creating agreement values"""
        return {
            'name': order.name,
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

    def action_button_generate_agreement(self):
        """Generates Purchase Recurring Agreement"""
        agreements = []
        agreement_obj = self.env['purchase.recurring.agreement']
        agreement_line_obj = self.env['recurring.agreement.line']
        for purchase_order in self:
            agreement_vals = self._prepare_agreement_vals(purchase_order)
            agreement = agreement_obj.create(agreement_vals)
            agreements.append(agreement)
            for order_id in purchase_order.order_line:
                agreement_line_vals = self._prepare_agreement_line_vals(
                    order_id, agreement)
                agreement_line_obj.create(agreement_line_vals)
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

    from_agreement = fields.Boolean(
        string='From Agreement?', copy=False,
        help='This field indicates if the purchase order comes from '
             'an agreement.')
    recurring_agreement_id = fields.Many2one('purchase.recurring.agreement',
                                             string='Agreement Reference',
                                             help="this indicates the Purchase "
                                                  "Agreement",
                                             ondelete='restrict')

    def view_order(self):
        """Returns the Corresponding Order"""
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'context': self.env.context,
            'res_id': self[:1].id,
            'view_id': [self.env.ref('purchase.purchase_order_form').id],
            'type': 'ir.actions.act_window',
            'nodestroy': True
        }
