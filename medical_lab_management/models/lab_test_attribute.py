# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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
#############################################################################
from odoo import fields, models


class LabTestAttribute(models.Model):
    """
       Model for managing lab test result
    """
    _name = 'lab.test.attribute'
    _description = "Lab Test Attributes"

    test_content = fields.Many2one('lab.test.content_type',
                                   string="Content")
    result = fields.Char(string="Result")
    unit = fields.Many2one('test.unit', string="Unit")
    interval = fields.Char(string="Reference Intervals")
    test_line_reverse = fields.Many2one('lab.test',
                                        string="Attribute")
    test_request_reverse = fields.Many2one('lab.request',
                                           string="Request")
