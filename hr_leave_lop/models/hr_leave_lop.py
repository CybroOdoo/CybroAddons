# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Fansa Jabeen A (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1) It is forbidden to publish, distribute, sublicense, or
#    sell copies of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
#    OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
#    THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrLeaveLOP(models.Model):
    """Model for Time Off LOP (Loss of Pay)"""
    _name = "hr.leave.lop"
    _description = "Time Off LOP"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", help="Set a name to Identify the LOP rule.",
                       required=True)
    leave_type = fields.Selection(
[
            ('before_holiday', 'Day Before Holiday'),
            ('after_holiday', 'Day After Holiday'),
            ('between_holidays', 'Between Holidays')
        ],
        string="Leave Type",
        required=True,
        help="Set type of leave to consider as lop "
             "\n\n'Day Before Holiday': Choose this option if the leave day "
             "falls just before a holiday, and it's considered as a loss of "
             "pay."
             "\n\n'Day After Holiday': Select this option if the leave day is "
             "immediately following a holiday and should be considered as a "
             "loss of pay."
             "\n\n'Between Holidays': Use this option when the leave spans "
             "between two holidays, and it's treated as a loss of pay.")
    deduction_amount = fields.Float(string='Deduction Amount %',
                                    help="Percentage of daily wage to be "
                                         "deducted", required=True)
    no_of_days = fields.Integer(string='Minimum Holidays',
                                help="Minimum number of consecutive holidays needed to trigger this LOP "
                                     "(used for Before and After holiday types)",
                                required=False)
    no_of_days_before = fields.Integer(string='Minimum Holidays Before',
                                       help="Minimum number of consecutive holidays required BEFORE the leave "
                                            "(used for Between Holidays type)",
                                       required=False)
    no_of_days_after = fields.Integer(string='Minimum Holidays After',
                                      help="Minimum number of consecutive holidays required AFTER the leave "
                                           "(used for Between Holidays type)",
                                      required=False)

    @api.constrains('no_of_days', 'no_of_days_before', 'no_of_days_after', 'leave_type')
    def _check_holiday_counts(self):
        """Ensure holiday counts are greater than 0 for the relevant types."""
        for record in self:
            if record.leave_type == 'between_holidays':
                if record.no_of_days_before <= 0 or record.no_of_days_after <= 0:
                    raise ValidationError(_("Holiday counts must be greater than 0 for 'Between Holidays' rules."))
            else:
                if record.no_of_days <= 0:
                    raise ValidationError(_("Minimum Holidays must be greater than 0."))

    def copy(self, default=None):
        """Prevent duplication of Time Off LOP records."""
        raise ValidationError(_("Cannot duplicate a Time Off LOP!"))
