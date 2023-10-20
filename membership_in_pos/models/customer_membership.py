"""Membership"""
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
from odoo import fields, models


class CustomerMembership(models.Model):
    """Creates membership types"""
    _name = 'customer.membership'
    _inherit = 'mail.thread'
    _description = 'Customer Membership'

    name = fields.Char(string='Name', required=True, help='Name')
    default_period = fields.Float(default=1, readonly="True",
                                  string='Default Validity Period(Year)',
                                  help='Default validity period in year')
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The membership name must be unique !')
    ]
