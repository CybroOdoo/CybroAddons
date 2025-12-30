# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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


class MachineConsume(models.Model):
    """This is the class for machine consume"""
    _name = 'machine.consume'
    _description = "Machine Consume"
    _rec_name = "consume_id"

    consume_id = fields.Many2one('machine.repair', string="Consumer",
                                 help="Reference to the machine repair record associated with this consumption.")
    machine_id = fields.Many2one('product.product', string='Machine',
                                 domain=[('is_machine', '=', True)],
                                 help="Select the machine being consumed. Only products marked as machines are available.")
    qty = fields.Float(string='Quantity',
                       help="The amount of the selected machine consumed in the repair or diagnosis process.")
    uom = fields.Many2one('uom.uom', string="UoM",
                          help="Unit of Measure for the quantity consumed.")
    dia_estimate_id = fields.Many2one('machine.diagnosis',
                                      string="Machine Diagnosis",
                                      help="Reference to the machine diagnosis record related to this consumption.")
    hour = fields.Float(string='Duration',
                        help="The number of hours the machine was used during the repair or diagnosis.")
