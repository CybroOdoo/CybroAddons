# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: fasluca(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import api, fields, models


class sale_discount(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('waiting', 'Waiting Approval'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    @api.multi
    def action_confirm(self):
        discnt = 0.0
        no_line = 0.0
        for order in self:
            if self.company_id.so_double_validation == 'two_step':
                for line in order.order_line:
                    no_line += 1
                    discnt += line.discount
                discnt = (discnt / no_line)
                if order.company_id.so_double_validation_limit and discnt > order.company_id.so_double_validation_limit:
                    order.state = 'waiting'
                    return True
            order._action_confirm()
            if order.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
                order.action_done()
        return True

    @api.multi
    def action_approve(self):
        self._action_confirm()
        if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
            self.action_done()
        return True


class Company(models.Model):
    _inherit = 'res.company'

    so_double_validation = fields.Selection([
        ('one_step', 'Confirm sale orders in one step'),
        ('two_step', 'Get 2 levels of approvals to confirm a sale order')
    ], string="Levels of Approvals", default='one_step',
        help="Provide a double validation mechanism for sales discount")

    so_double_validation_limit = fields.Float(string="Percentage of Discount that requires double validation'",
                                  help="Minimum discount percentage for which a double validation is required")


    # @api.multi
    # def set_default_discount(self):
    #     if self.discount_approval and self.discount_approval != self.company_id.discount_approval:
    #         self.company_id.write({'discount_approval': self.discount_approval})
    #     if self.limit_discount and self.limit_discount != self.company_id.limit_discount:
    #         self.company_id.write({'limit_discount': self.limit_discount})


class ResDiscountSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    so_order_approval = fields.Boolean("Sale Discount Approval", default=lambda self: self.env.user.company_id.so_double_validation == 'two_step')

    so_double_validation = fields.Selection(related='company_id.so_double_validation',)
                                            # help='Provide a double validation mechanism for sale exceeding maximum discount limit.')
    so_double_validation_limit = fields.Float(string="Discount limit requires approval in %",
                                              related='company_id.so_double_validation_limit')


    # @api.model
    # def get_values(self):
    #     res = super(ResDiscountSettings, self).get_values()
    #     res.update(
    #         limit_discount=self.company_id.limit_discount if self.company_id.limit_discount else 0.0,
    #         discount_approval=True if self.company_id.discount_approval else False
    #     )
    #     return res
    #
    # @api.multi
    # def set_values(self):
    #     super(ResDiscountSettings, self).set_values()
    #     self.company_id.limit_discount = self.limit_discount
    #     self.company_id.discount_approval = self.discount_approval

    def set_values(self):
        super(ResDiscountSettings, self).set_values()
        self.so_double_validation = 'two_step' if self.so_order_approval else 'one_step'