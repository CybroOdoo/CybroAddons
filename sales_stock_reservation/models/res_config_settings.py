# -*- coding: utf-8 -*-
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


class ResConfigSettings(models.TransientModel):
    """
    Inherits the Res Config Settings model to add two many-to-one fields for
    selecting source and destination locations. These fields are used to
    configure the source and destination locations for stock reservations.
    """
    _inherit = 'res.config.settings'

    source_location_id = fields.Many2one(
        "stock.location",
        config_parameter='sales_stock_reservation.source_location_id',
        help='Location from which products will be reserved.')
    destination_location_id = fields.Many2one(
        "stock.location",
        config_parameter='sales_stock_reservation.destination_location_id',
        help='Location to which products will be reserved.')
