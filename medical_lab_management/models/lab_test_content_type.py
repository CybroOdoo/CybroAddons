##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Maintainer: Cybrosys Technologies (<https://www.cybrosys.com>)
#
##############################################################################

from odoo import models, fields


class LabTestContentType(models.Model):
    _name = 'lab.test.content_type'
    _rec_name = 'content_type_name'
    _description = "Content"

    content_type_name = fields.Char(string="Name", required=True, help="Content type name")
    content_type_code = fields.Char(string="Code")
    parent_test = fields.Many2one('lab.test', string="Test Category")




