# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya B (odoo@cybrosys.com)
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
                                 help="Consumer of the repair")
    machine_id = fields.Many2one('product.product', string='Machine',
                                 help="Machine for consume",
                                 domain=[('is_machine', '=', True)])
    qty = fields.Float(string='Quantity', help="Quantity of the machine")
    uom = fields.Many2one('uom.uom', string="Uom", help="Machine uom")
    dia_estimate_id = fields.Many2one('machine.diagnosis',
                                      string="Machine Diagnosis",
                                      help="Diagnosis of machine")
    hour = fields.Float(string='Duration', help="Duration for the machine")
