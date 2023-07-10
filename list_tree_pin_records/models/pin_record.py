# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ruksana P (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class PinRecord(models.Model):
    """Class is used to store pinned recodes in the database"""
    _name = 'pin.record'
    _description = 'Pin Records'

    record = fields.Integer(string="Record Id", help='Id of pinned record')
    res_model = fields.Char(string="Model", help='Model of pinned record')
    color = fields.Char(string="Color", help='Color of pinned record')

    @api.model
    def save_pin_record(self, pin_model):
        """Function to create new records in specified model"""
        model = "'" + pin_model[1] + "'"
        record = self.search(
            [('record', '=', pin_model[0]), ('res_model', '=', model)])
        if record:
            record.unlink()
        else:
            self.create({
                'record': pin_model[0],
                'res_model': model,
                'color': pin_model[2],
            })
        result = self.search([('res_model', '=', model)])
        return result

    @api.model
    def pin_records(self, pin_model):
        """Function to fetch id of the specified model"""
        model = "'" + pin_model[0] + "'"
        records = self.search(
            [('res_model', '=', model)])
        if records:
            record = [rec.record for rec in records]
            return {'id': record}
