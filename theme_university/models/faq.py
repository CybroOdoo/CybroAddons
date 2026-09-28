# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
from odoo import models, fields


class UniversityFaq(models.Model):
    """Represents a frequently asked question and its answer displayed in the
    FAQ section of the website."""
    _name = 'university.faq'
    _description = 'University FAQ'
    _order = 'sequence, id'

    question = fields.Char('Question', required=True, translate=True,
                           help='The frequently asked question displayed to visitors.')
    answer = fields.Html('Answer', required=True, translate=True,
                         help='The answer to the question, supporting rich text formatting.')
    sequence = fields.Integer('Sequence', default=10,
                              help='Determines the display order of FAQs. Lower values appear first.')
