# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import fields, models


class FleetVehicle(models.Model):
    """
    Inherits from 'fleet.vehicle' to add additional fields and functionality.
    """
    _inherit = 'fleet.vehicle'

    status = fields.Selection([
        ('operational', 'Operational'),
        ('undermaintenance', 'Under Maintenance'),
    ], default='operational')
    rent_hour = fields.Float(string='Rent / Hour', help="Rent per hour")
    rent_day = fields.Float(string='Rent / Day', help="Rent per day")
    rent_kilometer = fields.Float(string='Rent / Kilometer',
                                  help="Rent per kilometer")
    charge_hour = fields.Float(string='Extra Charge / Hour',
                               help="Extra charge per hour")
    charge_day = fields.Float(string='Extra Charge / Day',
                              help="Extra charge per day")

    charge_kilometer = fields.Float(string='Extra Charge / Kilometer',
                                    help="Extra charge per kilometer")
