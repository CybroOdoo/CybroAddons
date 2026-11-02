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


class MachineConsume(models.Model):
    """This model stores the parts consumed in a repair or diagnosis."""
    _name = 'machine.consume'
    _description = "Machine Consume"
    _rec_name = "consume_id"

    consume_id = fields.Many2one('machine.repair', string="Machine Repair",
                                 help="Reference to the machine repair record associated with this consumption.")
    machine_id = fields.Many2one('product.product',
                                 domain=[('is_machine_parts', '=', True)],
                                 help="Select the spare part being consumed. Only products marked as machine parts are available.")
    qty = fields.Float(string='Quantity',
                       help="The amount of the selected spare part consumed in the repair or diagnosis process.")
    uom_id = fields.Many2one('uom.uom', string="UoM",
                             help="Unit of Measure for the quantity consumed.")
    dia_estimate_id = fields.Many2one('machine.diagnosis',
                                      string="Machine Diagnosis",
                                      help="Reference to the machine diagnosis record related to this consumption.")
    hour = fields.Float(string='Duration',
                        help="The number of hours the machine was used during the repair or diagnosis.")
