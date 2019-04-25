##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Maintainer: Cybrosys Technologies (<https://www.cybrosys.com>)
#
##############################################################################

from odoo import models, fields


class LabTestType(models.Model):
    _name = 'lab.test'
    _description = "Lab Test"
    _rec_name = 'lab_test'
    _inherit = ['mail.thread']

    lab_test = fields.Char(string="Test Name", required=True, help="Name of lab test ")
    lab_test_code = fields.Char(string="Test Code", required=True)
    test_lines = fields.One2many('lab.test.attribute', 'test_line_reverse', string="Attribute")
    test_cost = fields.Integer(string="Cost", required=True)


class LabTestAttribute(models.Model):
    _name = 'lab.test.attribute'

    test_content = fields.Many2one('lab.test.content_type', string="Content")
    result = fields.Char(string="Result")
    unit = fields.Many2one('test.unit', string="Unit")
    interval = fields.Char(string="Reference Intervals")
    test_line_reverse = fields.Many2one('lab.test', string="Attribute")
    test_request_reverse = fields.Many2one('lab.request', string="Request")
