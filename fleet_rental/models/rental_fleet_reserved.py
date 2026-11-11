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


class FleetReservedTime(models.Model):
    _name = "rental.fleet.reserved"
    _description = "Reserved Time"

    customer_id = fields.Many2one(comodel_name='res.partner', help='Select customer')
    date_from = fields.Date(string='Reserved Date From', help='Select the start date of rental ')
    date_to = fields.Date(string='Reserved Date To', help='Select the end date of rental')
    reserved_obj_id = fields.Many2one(comodel_name='fleet.vehicle', string='Reserved Object', help='Reserved Object')
