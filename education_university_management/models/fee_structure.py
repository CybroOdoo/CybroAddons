# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raneesha M K (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class FeeStructure(models.Model):
    """Managing the fee structure for university students"""
    _name = 'fee.structure'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Fees structure of university"

    name = fields.Char('Name', required=True,
                       help="Enter the name of fee structure")
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda
                                      self: self.env.user.company_id.currency_id.id,
                                  help="Currency of current company")
    structure_line_ids = fields.One2many('fee.structure.line',
                                         'fee_structure_id',
                                         string='Fee Types',
                                         help="Fee structure line")
    description = fields.Text(string="Additional Information",
                              help="Any additional information about")
    academic_year_id = fields.Many2one('university.academic.year',
                                       help="Choose academic year",
                                       string='Academic Year', required=True)
    amount_total = fields.Float(string="Amount", currency_field='currency_id',
                                help="Total amount of the lines",
                                required=True, compute='_compute_total')
    category_id = fields.Many2one('fee.category', string='Category',
                                  help="Select th category for structure",
                                  required=True)

    @api.depends('structure_line_ids.fee_amount')
    def _compute_total(self):
        """Method for computing total amount of the structure lines"""
        self.amount_total = sum(
            line.fee_amount for line in self.structure_line_ids)
