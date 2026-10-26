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
from odoo import api, fields, models


class HrEmployee(models.Model):
    """
    Inheriting hr_employee model to add a image field
    """
    _inherit = 'hr.employee'

    image = fields.Binary(string="Image", help="Add image for POS face login")

    @api.model
    def _load_pos_data_fields(self, config):
        pos_fields = super()._load_pos_data_fields(config)
        for field in ['image', 'image_1920', 'avatar_512']:
            if field not in pos_fields:
                pos_fields.append(field)
        return pos_fields
