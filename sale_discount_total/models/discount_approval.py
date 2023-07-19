# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Faslu Rahman(odoo@cybrosys.com)
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
#############################################################################

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
    ], string='Status', readonly=True, copy=False, index=True,
        track_visibility='onchange', default='draft')

    def action_confirm(self):
        discnt = 0.0
        no_line = 0.0
        if self.company_id.so_double_validation == 'two_step':
            for line in self.order_line:
                no_line += 1
                discnt += line.discount
            discnt = (discnt / no_line)
            if self.company_id.so_double_validation_limit and discnt > self.company_id.so_double_validation_limit:
                self.state = 'waiting'
                return True
        super(sale_discount, self).action_confirm()

    def action_approve(self):
        super(sale_discount, self).action_confirm()
        return True


class Company(models.Model):
    _inherit = 'res.company'

    so_double_validation = fields.Selection([
        ('one_step', 'Confirm sale orders in one step'),
        ('two_step', 'Get 2 levels of approvals to confirm a sale order')
    ], string="Levels of Approvals", default='one_step',
        help="Provide a double validation mechanism for sales discount")

    so_double_validation_limit = fields.Float(
        string="Percentage of Discount that requires double validation'",
        help="Minimum discount percentage for which a double validation is "
             "required")


class ResDiscountSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    so_order_approval = fields.Boolean("Sale Discount Approval", default=lambda
        self: self.env.user.company_id.so_double_validation == 'two_step')

    so_double_validation = fields.Selection(
        related='company_id.so_double_validation',
        string="Levels of Approvals *", readonly=False)
    so_double_validation_limit = fields.Float(
        string="Discount limit requires approval in %",
        related='company_id.so_double_validation_limit', readonly=False)

    def set_values(self):
        super(ResDiscountSettings, self).set_values()
        self.so_double_validation = 'two_step' if self.so_order_approval else 'one_step'
