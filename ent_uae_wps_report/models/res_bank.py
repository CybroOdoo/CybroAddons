# -*- coding: utf-8 -*-
################################################################################
#
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Harshitha AP (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from odoo import api, fields, models


class ResBank(models.Model):
    """Inherited to add field"""
    _inherit = 'res.bank'

    routing_code = fields.Char(string="Routing Code", size=9, required=True,
                               help="Bank Route Code")

    def write(self, vals):
        """To add routing code value while editing"""
        if 'routing_code' in vals.keys():
            vals['routing_code'] = vals['routing_code'].zfill(9)
        return super().write(vals)

    @api.model
    def create(self, vals):
        """To add routing code value while creating"""
        if 'routing_code' in vals.keys():
            vals['routing_code'] = vals['routing_code'].zfill(9)
        return super().create(vals)
