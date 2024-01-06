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
from odoo import api, fields, models, _
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
                             help="Enable if the student pass the exam",
                             default=False)
    valuation_id = fields.Many2one('exam.valuation',
                                   help="relation to exam valuation model",
                                   string='Valuation Id')

    @api.onchange('mark_scored', 'is_pass')
    def _onchange_mark_scored(self):
        """to determine whether the scored mark exceeds the subject's
          maximum mark and determine pass/fail depending on the scored mark."""
        if self.mark_scored > self.valuation_id.mark:
            raise UserError(_('Mark Scored must be less than Max Mark'))
        self.is_pass = True if \
            self.mark_scored >= self.valuation_id.pass_mark else False
