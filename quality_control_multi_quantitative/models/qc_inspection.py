# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2012-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nikhil krishnan(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import statistics
from openerp import models, fields, api, exceptions, _
from openerp.exceptions import Warning


class QcInspection(models.Model):
    _inherit = 'qc.inspection'

    # Replace this function here. for Checking the test_number and test_results
    @api.multi
    def action_confirm(self):
        for inspection in self:
            for line in inspection.inspection_lines:
                if line.question_type == 'qualitative':
                    if not line.qualitative_value:
                        raise exceptions.Warning(
                            _("You should provide an answer for all "
                              "qualitative questions."))
                else:
                    if not line.uom_id:
                        raise exceptions.Warning(
                            _("You should provide a unit of measure for"
                              "quantitative questions."))
                    if line.test_number == len(line.test_results):
                        pass
                    elif line.test_number > len(line.test_results):
                        raise exceptions.Warning(
                            _("Warning \n"
                              "Question %s has no sufficient test results. we need %s results" % (line.name,
                                                                                                  line.test_number)))
                    else:
                        raise exceptions.Warning(
                            _("Warning \n" "Question %s has excess of test results. Number of tests is %s. Please update "
                              "the test number  or test results" % (line.name, line.test_number)))

            if inspection.success:
                inspection.state = 'success'
            else:
                inspection.state = 'waiting'


class QcInspectionLine(models.Model):
    _inherit = 'qc.inspection.line'
    _description = 'Quality control inspection'

    @api.one
    @api.depends('question_type', 'test_number', 'test_results', 'test_method')
    def quantitative_value_check(self):
        if self.question_type == 'qualitative':
            # self.write({'test_number': 0})
            self.test_number = 0
        else:
            lst = []
            for n in self.test_results:
                lst.append(n.name)
            if self.test_method == 'avg_mean':
                if self.test_number == len(self.test_results):
                    self.quantitative_value = statistics.mean(lst)
                else:
                    self.quantitative_value = 0
            elif self.test_method == 'avg_mode':
                if self.test_number == len(self.test_results):
                    try:
                        self.quantitative_value = statistics.mode(lst)
                    except Exception, e:
                        raise Warning(_("Warning \n"
                                               "no unique mode; found %s equally common values" % (self.test_number)))
                else:
                    self.quantitative_value = 0
            elif self.test_method == 'avg_median':
                if self.test_number == len(self.test_results):
                    self.quantitative_value = statistics.median(lst)
                else:
                    self.quantitative_value = 0

            elif self.test_method == 'max_method':
                if self.test_number == len(self.test_results):
                    self.quantitative_value = max(lst)
                else:
                    self.quantitative_value = 0
            else:
                if self.test_number == len(self.test_results):
                    self.quantitative_value = min(lst)
                else:
                    self.quantitative_value = 0

    @api.one
    @api.depends('question_type', 'test_number', 'test_results', 'uom_id', 'test_uom_id', 'max_value',
                 'min_value', 'quantitative_value', 'qualitative_value',
                 'possible_ql_values')
    def quality_test_check(self):
        if self.question_type == 'qualitative':
            self.success = self.qualitative_value.ok
        else:
            if self.uom_id.id == self.test_uom_id.id:
                amount = self.quantitative_value
            else:
                amount = self.env['product.uom']._compute_qty(
                    self.uom_id.id, self.quantitative_value,
                    self.test_uom_id.id)
            self.success = self.max_value >= amount >= self.min_value

    test_number = fields.Integer('Number of tests', default=2)
    test_results = fields.Many2many('qc.test.results')
    quantitative_value = fields.Float(
        'Quantitative value', compute="quantitative_value_check", digits=(16, 5),
        help="Value of the result for a quantitative question.")
    test_method = fields.Selection([('avg_mean', 'Mean'), ('avg_mode', 'Mode'),
                                    ('avg_median', 'Median'), ('max_method', 'Largest'),
                                    ('min_method', 'Smallest')], 'Testing Method', default='avg_mean',
                                   help='The testing Method are used to calculate the Quantitative value with '
                                        'varies calculation methods.\n1-Mean: Sum of Test results divided by Number '
                                        'of tests.\n2- Mode: Results that occurs most often within the set '
                                        'of Test results.\n3-Median: Median is the middle Result in a sequence '
                                        'of Test results.\n4- Largest: Largest result from the Test results\n'
                                        '5-Smallest: Smallest result from the Test results)')


class QcTestResults(models.Model):
    _name = 'qc.test.results'

    name = fields.Float(string='Values')
