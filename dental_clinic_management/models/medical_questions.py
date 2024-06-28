# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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


class MedicalQuestions(models.Model):
    """To add medical questionnaire question"""
    _name = 'medical.questions'
    _description = 'Medical Questions'
    _rec_name = 'question'

    question = fields.Char(string='Question')

    @api.model
    def create(self, vals):
        """Overrides the default create method to add a new medical question
        record and automatically create a corresponding entry in the
        `medical.questionnaire` model."""
        res = super(MedicalQuestions, self).create(vals)
        self.env['medical.questionnaire'].create({
            'question_id': res.id
        })
        return res

    def unlink(self):
        """Overrides the default unlink method to delete the current medical question record.
        Before deletion, it searches for and deletes any associated records in the
        `medical.questionnaire` model that reference this medical question."""
        for rec in self:
            for line in self.env['medical.questionnaire'].search([('question_id', '=', rec.id)]):
                line.unlink()
            return super(MedicalQuestions, self).unlink()
