""""Pos membership"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri v (odoo@cybrosys.com)
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
from uuid import uuid4
from odoo import api, fields, models, _
from odoo import exceptions


class MembershipCard(models.Model):
    """Creating membership card for the customers"""
    _name = 'membership.card'
    _inherit = 'mail.thread'
    _description = 'Membership Card'
    _rec_name = 'membership_id'

    membership_id = fields.Many2one('customer.membership', string='Membership',
                                    required=True, help='Membership id')
    customer_id = fields.Many2one('res.partner', string="Customer",
                                  help='The customer')
    issue_date = fields.Date(string="Issue Date", help='Issue date')
    validity = fields.Float(string='Validity(days)',
                            compute='_compute_validity',
                            help='Validity of membership card')
    expiry_date = fields.Date(string="Exp Date", default=fields.Date.today(),
                              help='Expiry date of membership card')
    code = fields.Char(string="Code", help='Unique code for the card',
                       readonly=True)
    membership_code_button = fields.Boolean(default=False, string="Visibility",
                                            help='The code generation button visibility')
    discount = fields.Float(string='Discount(%)', help='Discount percentage amount')
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirm'), ('cancel', 'Cancel')],
        default='draft', string='State', help='State of the membership')

    @api.onchange('expiry_date')
    def _onchange_expiry_date(self):
        """This is used to check the expiry date of the membership"""
        if self.expiry_date < fields.Date.today():
            raise exceptions.ValidationError(_(
                "Please select a Valid Date."
            ))

    def generate_code(self):
        """Used to generate the code for membership card"""
        self.code = '550' + str(uuid4())[7:-18]
        self.membership_code_button = True

    def action_membership_confirm(self):
        """Used to confirm the membership"""
        self.state = 'confirm'

    def action_membership_canceled(self):
        """Cancels the membership"""
        self.state = 'cancel'

    def _compute_validity(self):
        """Computes the validity"""
        for rec in self:
            date = rec.expiry_date - rec.issue_date
            rec.validity = date.days

    def membership_card_check(self, customer_input):
        """Checks the validity of the membership card"""
        val = self.env['membership.card'].search(
            [('customer_id.id', '=', customer_input[0]['customer']),
             ('code', '=', customer_input[0]['customerInput']),
             ('expiry_date', '>', fields.Date.today()),
             ('state', '=', 'confirm')])
        membership_discount = self.env['membership.card'].sudo().search([(
            'customer_id.id', '=', customer_input[0]['customer'])]).mapped(
            'discount')
        membership_product = int(
            self.env['ir.config_parameter'].sudo().get_param(
                'pos_membership_product_id'))
        if val:
            return {
                'customer_name': val.customer_id.name,
                'membership': val.membership_id.name,
                'discount': membership_discount[0],
                'product_id': membership_product,
            }
        else:
            return 0
