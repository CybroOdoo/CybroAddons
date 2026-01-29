# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
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
###############################################################################
import re
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ServiceBooking(models.Model):
    """Service booking from the Frontend"""
    _name = "service.booking"
    _description = "Service booking"

    reference = fields.Char(
        string="Reference",
        help="unique reference for the service booking."
             "This can be an alphanumeric code.",
        copy=False)
    state = fields.Selection(
        [('draft', 'Draft'),
         ('running', 'Running'),
         ('cancel', 'Cancel'),
         ('done', 'Done')],
        help="Select the current state of the service booking.",
        default="draft")
    name = fields.Char(
        string='Name',
        help="Enter the name of the customer who made the service booking.")
    email = fields.Char(
        string='Email',
        help="Enter the email address of the customer. "
             "This will be used for communication.")
    description = fields.Char(
        string='Description',
        help="Provide a brief description of "
             "the service or any additional notes.")

    @api.model
    def create(self, vals):
        """Supering create function for creating sequence"""
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code(
                'reference.sequence') or _('New')
        return super(ServiceBooking, self).create(vals)

    @api.onchange('email')
    def validate_mail(self):
        """Function for checking the email entered in correct format"""
        if self.email:
            if not re.match(r"[^@]+@[^@]+\.[^@]+", self.email):
                raise ValidationError(_("Invalid email format. Please enter"
                                        " a valid email address."))
