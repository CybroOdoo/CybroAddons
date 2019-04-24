##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Maintainer: Cybrosys Technologies (<https://www.cybrosys.com>)
#
##############################################################################

from odoo import models, fields


class TestingUnit(models.Model):
    _name = 'test.unit'
    _rec_name = 'code'
    _description = "Test Unit"

    unit = fields.Char(string="Unit", required=True)
    code = fields.Char(string="code", required=True)
