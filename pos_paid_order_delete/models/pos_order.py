# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)

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
#############################################################################

from odoo import models, _
from odoo.addons.point_of_sale.models.pos_order import PosOrder
from odoo.exceptions import UserError
from odoo.tools import float_compare, formatLang


class PosOrderInherit(models.Model):
    '''Inherit the pos.order model to override the write method'''
    _inherit = 'pos.order'
    _description = "POS Order Inherit"

    def write(self, vals):
        '''Monkey patching the write method of pos.order to add extra condition for UserError'''
        is_delete = (self.env['ir.config_parameter'].sudo().get_param('pos_paid_order_delete.is_delete'))
        for order in self:
            if vals.get('state') and vals['state'] == 'paid' and order.name == '/':
                vals['name'] = self._compute_order_name()
            if vals.get('mobile'):
                vals['mobile'] = order._phone_format(number=vals.get('mobile'),
                        country=order.partner_id.country_id or self.env.company.country_id)
            if vals.get('has_deleted_line') is not None and self.has_deleted_line:
                del vals['has_deleted_line']
            allowed_vals = ['paid', 'done', 'invoiced']
            if vals.get('state') and vals['state'] not in allowed_vals and order.state in allowed_vals and not is_delete:
                raise UserError(_('This order has already been paid. You cannot set it back to draft or edit it.'))

        list_line = self._create_pm_change_log(vals)

        res = super(PosOrder, self).write(vals)
        for order in self:
            if vals.get('payment_ids'):
                order.with_context(backend_recomputation=True)._compute_prices()
                totally_paid_or_more = float_compare(order.amount_paid, self._get_rounded_amount(order.amount_total), precision_rounding=order.currency_id.rounding)
                if totally_paid_or_more < 0 and order.state in ['paid', 'done', 'invoiced']:
                    raise UserError(_('The paid amount is different from the total amount of the order.'))
                elif totally_paid_or_more > 0 and order.state == 'paid':
                    list_line.append(_("Warning, the paid amount is higher than the total amount. (Difference: %s)", formatLang(self.env, order.amount_paid - order.amount_total, currency_obj=order.currency_id)))
                if order.nb_print > 0 and vals.get('payment_ids'):
                    raise UserError(_('You cannot change the payment of a printed order.'))

        if len(list_line) > 0:
            body = _("Payment changes:")
            body += self._markup_list_message(list_line)
            for order in self:
                if vals.get('payment_ids'):
                    order.message_post(body=body)
        return res

    PosOrder.write = write
