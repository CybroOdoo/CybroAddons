# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: MOHAMMED DILSHAD TK (odoo@cybrosys.com)
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
from odoo import fields, models


class FieldWidgets(models.Model):
    """We can't filter a selection field dynamically
       so when we select a field its widgets also need to change according to
       the selected field type, we can't do it by a 'selection' field,
       need a 'Many 2 one' field."""

    _name = 'dynamic.field.widgets'
    _rec_name = 'description'
    _description = 'Field Widgets'

    name = fields.Char(string="Name", help="Technical name of the widget")
    data_type = fields.Char(string="Data Type", help="Datatype suitable for"
                                                     " the widget")
    description = fields.Char(string="Description", help="Description of"
                                                         " the widget")
