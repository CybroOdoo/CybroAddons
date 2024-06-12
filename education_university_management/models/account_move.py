# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Jabin MP (odoo@cybrosys.com)
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
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    """Inheriting account move model for creating receipt for students fees"""
    _inherit = 'account.move'

    student_id = fields.Many2one('university.student',
                                 string='Admission No',
                                 help="Select student for creating fee "
                                      "receipt")
    student_name = fields.Char(string='Name',
                               help="Student name that your going to "
                                    "make receipt", store=True,
                               related='student_id.partner_id.name')
    semester_id = fields.Many2one(related='student_id.semester_id',
                                  help="Semester of the student",
                                  string='Semester')
    batch_id = fields.Many2one(related='student_id.batch_id',
                               help="batch of the student", )
    fee_structure_id = fields.Many2one('fee.structure',
                                       help="Select a fee structure",
                                       string='Fee Structure')
    fee_structure_ids = fields.Many2many('fee.structure',
                                         string="Fee Structure",
                                         compute="_compute_fee_structure_ids",
                                         help="Select a fee structure", )
    is_fee = fields.Boolean(string='Is Fee', store=True, default=False,
                            help="To determine whether the account "
                                 "move is for fee or not")
    fee_category_id = fields.Many2one('fee.category',
                                      help="Select a fee category",
                                      string='Category')
    partner_id = fields.Many2one(related='student_id.partner_id',
                                 help="Set student partner in customer", )
    journal_id = fields.Many2one(related='fee_category_id.journal_id',
                                 help="Journal of the receipt")

    @api.model_create_multi
    def create(self, vals):
        """ This method overrides the create method to add two fields to the
            invoice: 'is_fee' and 'student_name'.The 'is_fee' field is used to
            display fee items only in the fee tree view.
            :param vals (dict): Dictionary containing the field values for the
                                new invoice record.
            :returns class:`~account.move`: The created invoice record.
        """
        partner = self.env['res.partner'].browse(vals[0].get('partner_id'))
        if vals[0].get('fee_category_id'):
            vals[0].update({
                'is_fee': True,
                'student_name': partner.name
            })
        res = super(AccountMove, self).create(vals)
        return res

    @api.onchange('fee_structure_id')
    def _onchange_fee_structure_id(self):
        """Set default fee lines based on selected fee structure"""
        lines = []
        self.invoice_line_ids = False
        for item in self:
            for line in item.fee_structure_id.structure_line_ids:
                name = line.fee_type_id.product_id.description_sale
                if not name:
                    name = line.fee_type_id.product_id.name
                fee_line = {
                    'price_unit': line.fee_amount,
                    'quantity': 1.00,
                    'product_id': line.fee_type_id.product_id,
                    'name': name,
                    'account_id': item.journal_id.default_account_id
                }
                lines.append((0, 0, fee_line))
            item.invoice_line_ids = lines

    @api.depends('fee_category_id')
    def _compute_fee_structure_ids(self):
        """ To find the fee structure in the selected category and assign them
            to fee_structure_ids field for setting domain for
            fee_category_id field """
        for rec in self:
            if rec.fee_category_id:
                rec.fee_structure_ids = self.env['fee.structure'].search(
                    [('category_id', '=', rec.fee_category_id.id)]).ids
                if not rec.fee_structure_ids:
                    raise ValidationError(
                        _("No Fee Structure found for selected Category, "
                          "Please choose another one"))
            else:
                rec.fee_structure_ids = False
