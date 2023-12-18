# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class SalonService(models.Model):
    """Creates 'salon.service' to store salon services"""
    _name = 'salon.service'
    _description = 'Salon Service'

    name = fields.Char(string="Name", required=True, help="Name of service")
    currency_id = fields.Many2one(comodel_name='res.currency',
                                  string='Currency', required=True,
                                  default=lambda self: self.env
                                  .user.company_id.currency_id.id,
                                  help="Currency for the service")
    price = fields.Monetary(string="Price", help="Amount for the service",
                            required=True)
    time_taken = fields.Float(string="Time", help="Approximate time required "
                                                  "for this service in Hours")
