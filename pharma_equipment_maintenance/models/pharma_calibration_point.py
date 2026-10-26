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
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare

RESULT = [('pass', 'Within Tolerance'), ('fail', 'Out of Tolerance')]


class PharmaCalibrationPoint(models.Model):
    """One check point of a calibration: standard used, readings and tolerance.

    Lines are optional. A site that attaches the external service's
    certificate still enters the points the certificate reports: they decide
    whether the calibration passed.
    """
    _name = 'pharma.calibration.point'
    _description = 'Calibration Check Point'
    _order = 'result_id, sequence, id'

    result_id = fields.Many2one(
        comodel_name='pharma.calibration.result', string='Calibration Result',
        required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    nominal_value = fields.Float(
        digits=(16, 4), required=True,
        help='Value of the certified standard applied, e.g. 100 for a 100 g weight.')
    unit = fields.Char(help='Unit of the readings, e.g. g, pH, C.')
    as_found = fields.Float(
        string='As-Found', digits=(16, 4), required=True,
        help='What the instrument read before any adjustment.')
    as_left = fields.Float(
        string='As-Left', digits=(16, 4), required=True,
        help='What the instrument read after adjustment. Enter the as-found '
             'value again when no adjustment was needed.')
    tolerance = fields.Float(
        string='Tolerance (+/-)', digits=(16, 4), required=True,
        help='Allowed deviation from the nominal value, in either direction.')
    as_found_deviation = fields.Float(
        string='As-Found Deviation', digits=(16, 4), compute='_compute_deviation', store=True)
    as_left_deviation = fields.Float(
        string='As-Left Deviation', digits=(16, 4), compute='_compute_deviation', store=True)
    as_found_result = fields.Selection(
        selection=RESULT, string='As-Found Result', compute='_compute_deviation', store=True)
    as_left_result = fields.Selection(
        selection=RESULT, string='As-Left Result', compute='_compute_deviation', store=True)

    @api.depends('nominal_value', 'as_found', 'as_left', 'tolerance')
    def _compute_deviation(self):
        """Deviation of each reading from the standard, and whether it is within tolerance."""
        for point in self:
            point.as_found_deviation = point.as_found - point.nominal_value
            point.as_left_deviation = point.as_left - point.nominal_value
            point.as_found_result = point._tolerance_result(point.as_found_deviation)
            point.as_left_result = point._tolerance_result(point.as_left_deviation)

    def _tolerance_result(self, deviation):
        """Whether ``deviation`` is within the tolerance of the point.

        :param deviation: reading minus the nominal value
        :return: 'pass' or 'fail'
        """
        self.ensure_one()
        within = float_compare(abs(deviation), self.tolerance, precision_digits=4) <= 0
        return 'pass' if within else 'fail'

    @api.constrains('tolerance')
    def _check_tolerance(self):
        """A zero or negative tolerance would fail or pass every reading."""
        for point in self:
            if point.tolerance <= 0:
                raise ValidationError(self.env._('The tolerance of a check point must be greater than zero.'))

    # ------------------------------------------------------------------
    # The points are a record of the work: editable only while it is open.
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Add points only to an open calibration."""
        points = super().create(vals_list)
        points.result_id._check_open()
        return points

    def write(self, vals):
        """Change points only on an open calibration, and never move them to a closed one."""
        self.result_id._check_open()
        res = super().write(vals)
        self.result_id._check_open()
        return res

    def unlink(self):
        """Remove points only from an open calibration."""
        self.result_id._check_open()
        return super().unlink()
