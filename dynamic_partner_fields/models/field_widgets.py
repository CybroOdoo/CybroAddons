# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Ajmal JK (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import api, models, fields, _


class FieldWidgets(models.Model):
    """We can't filter a selection field dynamically
       so when we select a field its widgets also need to change according to the selected
       field type, we can't do it by a 'selection' field, need a 'Many2one' field.
    """

    _name = 'partner.field.widgets'
    _rec_name = 'description'
    _description = 'Field Widgets'

    name = fields.Char(string="Name")
    description = fields.Char(string="Description")
