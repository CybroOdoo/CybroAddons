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


class HrEmployee(models.Model):
    """Inherited the model to add fields"""
    _inherit = 'hr.employee'

    labour_card_number = fields.Char(string="Employee Card Number", size=14,
                                     required=True,
                                     help="Labour Card Number Of Employee")
    salary_card_number = fields.Char(string="Salary Card Number/Account Number",
                                     size=16, required=True,
                                     help="Salary card number or account number"
                                          " of employee")
    agent_id = fields.Many2one('res.bank', string="Agent/Bank",
                               required=True, help="Agent ID or bank ID of"
                                                   " Employee")

    def write(self, vals):
        """To add labour card no. and salary card no. while editing"""
        if 'labour_card_number' in vals.keys():
            if len(vals['labour_card_number']) < 14:
                vals['labour_card_number'] = vals['labour_card_number'].zfill(
                    14)
        if 'salary_card_number' in vals.keys():
            if len(vals['salary_card_number']) < 16:
                vals['salary_card_number'] = vals['salary_card_number'].zfill(
                    16)
        return super().write(vals)

    @api.model
    def create(self, vals):
        """To add labour card no. and salary card no. while creating"""
        if 'labour_card_number' in vals.keys():
            if len(vals['labour_card_number']) < 14:
                vals['labour_card_number'] = vals['labour_card_number'].zfill(
                    14)
        if 'salary_card_number' in vals.keys():
            if len(vals['salary_card_number']) < 16:
                vals['salary_card_number'] = vals['salary_card_number'].zfill(
                    16)
        return super().create(vals)
