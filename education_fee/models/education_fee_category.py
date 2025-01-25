# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gayathri V (odoo@cybrosys.com)
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
from odoo import fields, models


class EducationFeeCategory(models.Model):
    """Creating model 'education.fee.category' and adding fields"""
    _name = 'education.fee.category'
    _description = 'Education Fee Category'

    name = fields.Char(string='Name', required=True,
                       help='Create a fee category suitable for your '
                            'institution. Like Institutional, Hostel, '
                            'Transportation, Arts and Sports, etc')
    journal_id = fields.Many2one('account.journal',
                                 string='Journal', required=True,
                                 help='Setting up of unique journal for each '
                                      'category help to distinguish '
                                      'account entries of each category ')
    fee_structure = fields.Boolean(string='Have a Fee Structure?',
                                   required=True,
                                   help='If any fee structure want to be '
                                        'included in this category '
                                        'you must click here.'
                                        'For an example Institution '
                                        'category have different kind of'
                                        ' fee structures '
                                        'for different syllabuses')
