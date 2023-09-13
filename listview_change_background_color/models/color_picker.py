# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Albin P J (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models


class ColorPicker(models.Model):
    """We can store the fields on this model temporarily and used to save"""
    _name = 'color.picker'
    _description = "Color Picker"

    record_id = fields.Integer(string="Record Id", help='Record id of color')
    res_model = fields.Char(string="Model", help='Corresponding model')
    color = fields.Char(string="Color", help='Color code')

    @api.model
    def get_color_picker_model_and_id(self, **kw):
        """We can get the all records, models and colors"""
        record = self.search([('record_id', '=', kw['record_id']),
                              ('res_model', '=', kw['model_name'])])
        if record:
            record.write({'color': kw['record_color']})
        else:
            self.create({
                'record_id': kw['record_id'],
                'res_model': kw['model_name'],
                'color': kw['record_color'],
            })
