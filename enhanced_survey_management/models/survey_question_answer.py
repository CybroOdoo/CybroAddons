# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Savad, Ahammed Harshad  (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import fields, models


class SurveyQuestionAnswer(models.Model):
    """Inherit question answer model to add new answer type and model field"""
    _inherit = 'survey.question.answer'

    answer_type = fields.Selection([
        ('text_box', 'Multiple Lines Text Box'),
        ('char_box', 'Single Line Text Box'),
        ('numerical_box', 'Numerical Value'),
        ('date', 'Date'),
        ('datetime', 'Datetime'),
        ('time', 'Time'),
        ('email', 'Email'),
        ('password', 'Password'),
        ('range', 'Range'),
        ('month', 'Month'),
        ('url', 'URL'),
        ('week', 'Week'),
        ('color', 'Color'),
        ('many2one', 'Many2one')], help="Answer type",
        string='Answer Type', readonly=False, store=True)
    model_id = fields.Many2one('ir.model', string='Model',
                               domain=[('transient', '=', False)],
                               help="Select model for getting it's"
                                    " values in survey")
