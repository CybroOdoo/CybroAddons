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


class FieldWidget(models.Model):
    """ Need of this model is because we can't filter a selection field
    dynamically so when we select a field its widgets also need to change
    according to field type, this cannot be achieved using a 'selection' field;
    we require a 'Many2one' field."""
    _name = 'field.widget'
    _description = 'Field Widget'
    _rec_name = 'description'

    name = fields.Char(help="Name of widget")
    description = fields.Char(help="Description of widget")
    data_type = fields.Char(help="Type of field")
