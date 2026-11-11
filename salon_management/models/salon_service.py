#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models


class SalonService(models.Model):
    """Creates 'salon.service' to store salon services"""
    _name = 'salon.service'
    _description = 'Salon Service'

    name = fields.Char(required=True, help="Name of service")
    currency_id = fields.Many2one(comodel_name='res.currency',
                                  required=True,
                                  default=lambda self: self.env
                                  .company.currency_id.id,
                                  help="Currency for the service")
    price = fields.Monetary(help="Amount for the service",
                            required=True)
    time_taken = fields.Float(string="Time", help="Approximate time required "
                                                  "for this service in Hours")
