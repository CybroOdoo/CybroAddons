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

    coa_id = fields.Many2one(
        'pharma.coa',
        string='CoA',
        required=True,
        ondelete='cascade',
        help='Certificate this result line belongs to.',
    )
    parameter = fields.Char(
        help='Name of the tested parameter.',
    )
    expected_min = fields.Float(
        help='Lower specification limit.',
    )
    expected_max = fields.Float(
        help='Upper specification limit.',
    )
    actual_value = fields.Float(
        help='Measured value.',
    )
    uom = fields.Char(
        string='UoM',
        help='Unit of measure of the values.',
    )
    status = fields.Selection(
        [
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('oos', 'OOS'),
            ('pending', 'Pending'),
        ],
        help='Outcome of the test against its limits; Pending when no value was recorded.',
    )
