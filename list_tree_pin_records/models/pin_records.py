# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class PinRecord(models.Model):
    """Class is used to store pinned recodes in the database"""
    _name = 'pin.records'
    _description = 'Pin Records'

    record_id = fields.Integer(string="Record Id", help='Record id')
    res_model = fields.Char(string="Model", help='Corresponding model')
    color = fields.Char(string="Color", help='Color code')
    user_id = fields.Many2one('res.users', string='User',
                              help="Set current user")

    @api.model
    def save_pin_record(self, pin_model):
        """Function to fetch data from XML"""
        record = self.search([('record_id', '=', pin_model[0]), ('res_model', '=', pin_model[1])])
        if record:
            record.unlink()
        else:
            self.create({
                'record_id': pin_model[0],
                'res_model': pin_model[1],
                'color': pin_model[2],
                'user_id': self.env.uid
            })
        result = self.search([('res_model', '=', pin_model)])
        return result

    @api.model
    def pin_record(self, pin_model):
        """Function to fetch id and color of the specified model"""
        pinned_record = []
        record_ids = self.search([('res_model', '=', pin_model),
                                  ('user_id', '=', self.env.uid)])
        for record_id in record_ids:
            pinned_record.append({
                'id': record_id.record_id,
                'color': record_id.color,
                'model': record_id.res_model
            })
        return pinned_record
