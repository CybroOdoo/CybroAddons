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
from odoo import api, fields, models


class CarRentalChecklist(models.Model):
    """Model to add the checklist of rental"""
    _name = 'car.rental.checklist'
    _description = "Checklist for car rental"

    name = fields.Many2one(comodel_name='car.tools',
                           help='Select car tools')
    checklist_active = fields.Boolean(string="Available",
                                      default=True,
                                      help='Enable when the tool is available while checking')
    checklist_number = fields.Many2one(comodel_name='car.rental.contract',
                                       help='Number of checklist')
    price = fields.Float(help='Price of the car tool')
    company_id = fields.Many2one(comodel_name='res.company',
                                 default=lambda self: self.env.company,
                                 help="Company this record owns")

    @api.onchange('name')
    def onchange_name(self):
        """ Update the price based on the selected name. """
        self.price = self.name.price
