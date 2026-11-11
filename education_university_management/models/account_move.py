# pylint: disable=unknown-option-value,missing-module-docstring
# pylint: disable=attribute-string-redundant
###############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models
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
                               help="batch of the student")
    fee_structure_id = fields.Many2one('fee.structure',
                                       help="Select a fee structure",
                                       string='Fee Structure')
    fee_structure_ids = fields.Many2many('fee.structure',
                                         string="Fee Structure",
                                         compute="_compute_fee_structure_ids",
                                         help="Select a fee structure")
    is_fee = fields.Boolean(string='Is Fee', store=True,
                            help="To determine whether the account "
                                 "move is for fee or not")
    fee_category_id = fields.Many2one('fee.category',
                                      help="Select a fee category",
                                      string='Category')

    @api.model_create_multi
    def create(self, vals):
        """ This method overrides the create method to add two fields to the
            invoice: 'is_fee' and 'student_name'.The 'is_fee' field is used to
            display fee items only in the fee tree view.
            :param vals (dict): Dictionary containing the field values for the
                                new invoice record.
            :returns class:`~account.move`: The created invoice record.
        """
        for rec in vals:
            if rec.get('student_id') and not rec.get('partner_id'):
                student = self.env['university.student'].browse(
                    rec.get('student_id'),
                )
                if student.partner_id:
                    rec['partner_id'] = student.partner_id.id
            if rec.get('fee_category_id') and not rec.get('journal_id'):
                fee_cat = self.env['fee.category'].browse(
                    rec.get('fee_category_id'),
                )
                if fee_cat.journal_id:
                    rec['journal_id'] = fee_cat.journal_id.id
            partner = self.env['res.partner'].browse(rec.get('partner_id'))
            if rec.get('fee_category_id'):
                rec.update({
                    'is_fee': True,
                    'student_name': partner.name,
                })
        return super().create(vals)

    @api.onchange('student_id')
    def _onchange_student_id(self):
        """Set partner from student"""
        if self.student_id and self.student_id.partner_id:
            self.partner_id = self.student_id.partner_id

    def onchange_student_id(self):
        """Public alias for _onchange_student_id"""
        return self._onchange_student_id()

    @api.onchange('fee_category_id')
    def _onchange_fee_category_id(self):
        """Set journal from fee category"""
        if self.fee_category_id and self.fee_category_id.journal_id:
            self.journal_id = self.fee_category_id.journal_id

    def onchange_fee_category_id(self):
        """Public alias for _onchange_fee_category_id"""
        return self._onchange_fee_category_id()

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
                    'product_id': line.fee_type_id.product_id.id,
                    'name': name,
                }
                if item.journal_id.default_account_id:
                    fee_line['account_id'] = item.journal_id.default_account_id.id
                lines.append(fields.Command.create(fee_line))
            item.invoice_line_ids = lines

    def onchange_fee_structure_id(self):
        """Public alias for _onchange_fee_structure_id"""
        return self._onchange_fee_structure_id()

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
                        self.env._(
                            "No Fee Structure found for selected Category, "
                            "Please choose another one",
                        ),
                    )
            else:
                rec.fee_structure_ids = False
