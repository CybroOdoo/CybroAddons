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


class LabTestContentType(models.Model):
    """
       Model for managing test content types
    """
    _name = 'lab.test.content.type'
    _rec_name = 'content_type_name'
    _description = "Content"

    content_type_name = fields.Char(string="Name", required=True,
                                    help="Content type name")
    content_type_code = fields.Char(string="Code", help="Content type code")
    parent_test_id = fields.Many2one('lab.test',
                                  string="Test Category",
                                  help="Category of test")
