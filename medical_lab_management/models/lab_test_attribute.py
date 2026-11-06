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


class LabTestAttribute(models.Model):
    """
       Model for managing lab test result
    """
    _name = 'lab.test.attribute'
    _description = "Lab Test Attributes"

    test_content_id = fields.Many2one('lab.test.content.type',
                                   string="Content", help="Content type", required=True)
    result = fields.Char(help="Result for lab test")
    unit_id = fields.Many2one('test.unit',
                           help="Unit for lab test")
    interval = fields.Char(string="Reference Intervals",
                           help="Reference intervals for lab test")
    test_line_reverse_id = fields.Many2one('lab.test',
                                        string="Attribute",
                                        help="Name of the test")
    test_request_reverse_id = fields.Many2one('lab.request',
                                           string="Request")
