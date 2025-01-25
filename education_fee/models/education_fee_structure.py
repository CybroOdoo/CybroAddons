# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gayathri V (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class EducationFeeStructure(models.Model):
    """Creating model 'education.fee.structure'"""
    _name = 'education.fee.structure'
    _description = 'Education Fee Structure'
    _rec_name = 'fee_structure_name'

    @api.depends('fee_type_ids.fee_amount')
    def compute_total(self):
        self.amount_total = sum(line.fee_amount for line in self.fee_type_ids)

    company_currency_id = fields.Many2one('res.currency',
                                          string='Company Currency',
                                          compute='get_company_id',
                                          readonly=True, related_sudo=False,
                                          help='Company currency')
    fee_structure_name = fields.Char(string='Name', required=True,
                                     help='Name of fee structure')
    fee_type_ids = fields.One2many('education.fee.structure.lines',
                                   'fee_structure_id',
                                   string='Fee Types', help='Specify the '
                                                            'fee types.')
    comment = fields.Text(string='Additional Information',
                          help="Additional information regarding the fee"
                               " structure")
    academic_year_id = fields.Many2one('education.academic.year',
                                       string='Academic Year', required=True,
                                       help='Mention the academic year.')
    expire = fields.Boolean(string='Expire',
                            help='Expired or not')
    amount_total = fields.Float(string='Amount',
                                currency_field='company_currency_id',
                                required=True, compute='compute_total',
                                help='Total amount')
    category_id = fields.Many2one('education.fee.category',
                                  string='Category', required=True,
                                  default=lambda self: self.env[
                                      'education.fee.category'].search([],
                                                                       limit=1),
                                  domain=[('fee_structure', '=', True)],
                                  help='Fees category.')
