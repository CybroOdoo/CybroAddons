# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models


class PharmaCoaLine(models.Model):
    """A single line of a Certificate of Analysis."""
    _name = 'pharma.coa.line'
    _description = 'CoA Result Line'

    coa_id = fields.Many2one('pharma.coa', string='CoA', required=True, ondelete='cascade',
                             help='Specifies the CoA for this record.')
    parameter = fields.Char(
        string='Parameter',
        help='Specifies the Parameter for this record.',
    )
    expected_min = fields.Float(
        string='Expected Min',
        help='Specifies the Expected Min for this record.',
    )
    expected_max = fields.Float(
        string='Expected Max',
        help='Specifies the Expected Max for this record.',
    )
    actual_value = fields.Float(
        string='Actual Value',
        help='Specifies the Actual Value for this record.',
    )
    uom = fields.Char(
        string='UoM',
        help='Specifies the UoM for this record.',
    )
    status = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('oos', 'OOS')
    ], string='Status', help='Specifies the Status for this record.')
