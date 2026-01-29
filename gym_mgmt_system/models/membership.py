# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Shahul Faiz (<https://www.cybrosys.com>)
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

from odoo import api, fields, models, _


class GymMembership(models.Model):
    _name = "gym.membership"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Gym Membership"
    _rec_name = "reference"

    reference = fields.Char(string='GYM reference', required=True,
                            readonly=True, default=lambda self: _('New'))
    member = fields.Many2one('res.partner', string='Member', required=True,
                             tracking=True,
                             domain="[('gym_member', '!=',False)]")
    membership_scheme = fields.Many2one('product.product',
                                        string='Membership scheme',
                                        required=True, tracking=True,
                                        domain="[('membership_date_from', '!=',False)]")
    paid_amount = fields.Integer(string="Paid Amount", tracking=True)
    membership_fees = fields.Float(string="Membership Fees", tracking=True,
                                   related="membership_scheme.list_price")
    sale_order_id = fields.Many2one('sale.order', string='Sales Order',
                                    ondelete='cascade', copy=False,
                                    readonly=True)
    membership_date_from = fields.Date(string='Membership Start Date',
                                       related="membership_scheme.membership_date_from",
                                       help='Date from which membership becomes active.')
    membership_date_to = fields.Date(string='Membership End Date',
                                     related="membership_scheme.membership_date_to",
                                     help='Date until which membership remains active.')

    _sql_constraints = [
        ('membership_date_greater',
         'check(membership_date_to >= membership_date_from)',
         'Error ! Ending Date cannot be set before Beginning Date.')
    ]
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('cancelled', 'Cancelled')
    ], default='draft', string='Status')

    @api.model
    def create(self, vals):
        """ sequence number for membership """
        if vals.get('reference', ('New')) == ('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code(
                'gym.membership') or ('New')
        res = super(GymMembership, self).create(vals)
        return res


class SaleConfirm(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        """ membership  created directly from sale order confirmed """
        product = self.env['product.product'].search([
            ('membership_date_from', '!=', False),
            ('id', '=', self.order_line.product_id.id)])
        for record in product:
            self.env['gym.membership'].create([
                {'member': self.partner_id.id,
                 'membership_date_from': record.membership_date_from,
                 'membership_scheme': self.order_line.product_id.id,
                 'sale_order_id': self.id,
                 }])

        res = super(SaleConfirm, self).action_confirm()
        return res
