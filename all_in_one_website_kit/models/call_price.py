# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class CallPrice(models.Model):
    """Creating a model to record all the request the get from website."""
    _name = 'call.price'
    _description = 'Call for Price'
    _rec_name = 'product_id'

    first_name = fields.Char(string="First Name", help="First Name of user")
    last_name = fields.Char(string="Last Name", help="Last Name of user")
    product_id = fields.Many2one('product.template', string="Product",
                                 help="In which product "
                                      "they are requesting price")
    email = fields.Char(string="Email", help="Users email for contact")
    phone = fields.Char(string="Contact No.",
                        help="Users contact number for contacting")
    quantity = fields.Integer(string="Quantity",
                              help="How much quantity of product price "
                                   "they want know")
    message = fields.Char(string="Message",
                          help="If any messages for referring")
    state = fields.Selection(
        [('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancel')],
        default="draft", help="Call for price requests stage", string="State")

    def action_done(self):
        """the price of the requested product will be updated for them,
        form state is done"""
        self.write({'state': 'done'})

    def action_cancel(self):
        """ cancel the form or change the state to cancel"""
        self.write({'state': 'cancel'})

    @api.model
    def create_form(self, first, last, product_id, phone, email, message, qty):
        """ create the request from the users to backend for teams"""
        self.create({
            'product_id': product_id,
            'first_name': first,
            'last_name': last,
            'phone': phone,
            'email': email,
            'quantity': qty,
            'message': message
        })
