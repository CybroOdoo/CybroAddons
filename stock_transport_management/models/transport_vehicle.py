# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Saritha Sahadevan(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api


class VehicleCreation(models.Model):
    _name = 'sale.vehicle'

    name = fields.Char(string="Vehicle Name", required=True)
    driver_name = fields.Many2one('res.partner', string="Contact Name", required=True)
    vehicle_image = fields.Binary(string='Image', store=True, attachment=True)
    licence_plate = fields.Char(string="Licence Plate", required=True)
    mob_no = fields.Char(string="Mobile Number", required=True)
    vehicle_address = fields.Char(string="Address")
    vehicle_city = fields.Char(string='City')
    vehicle_zip = fields.Char(string='ZIP')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country')
    active_available = fields.Boolean(string="Active", default=True)

    @api.one
    def complete_name_compute(self):
        self.name = self.ref_name
        if self.licence_plate:
            self.name = str(self.licence_plate) + ' / ' + str(self.ref_name)

