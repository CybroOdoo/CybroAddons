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
from odoo.exceptions import UserError


class ExamValuationLine(models.Model):
    """Used to record the students pass mark details while valuing the exam"""
    _name = 'exam.valuation.line'
    _description = 'Exam Valuation Line'

    student_id = fields.Many2one('university.student',
                                 string='Students',
                                 help="Students of batch")
    mark_scored = fields.Float(string='Mark',
                               help="Scored mark of the student")
    is_pass = fields.Boolean(string='Pass/Fail',
                             compute='_compute_is_pass',
                             store=True, readonly=False,
                             help="Enable if the student pass the exam")
    valuation_id = fields.Many2one('exam.valuation',
                                   help="relation to exam valuation model",
                                   string='Valuation Id')

    @api.depends('mark_scored', 'valuation_id.pass_mark')
    def _compute_is_pass(self):
        for rec in self:
            if rec.valuation_id and rec.valuation_id.pass_mark:
                rec.is_pass = rec.mark_scored >= rec.valuation_id.pass_mark
            else:
                rec.is_pass = False

    @api.onchange('mark_scored', 'is_pass')
    def _onchange_mark_scored(self):
        """to determine whether the scored mark exceeds the subject's
          maximum mark and determine pass/fail depending on the scored mark."""
        if self.mark_scored > self.valuation_id.mark:
            raise UserError(
                self.env._('Mark Scored must be less than Max Mark'),
            )
        self.is_pass = self.mark_scored >= self.valuation_id.pass_mark
