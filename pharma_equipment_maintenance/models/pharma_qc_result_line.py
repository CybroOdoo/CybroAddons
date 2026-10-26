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

CALIBRATION_OK = ('ok', 'due_soon', 'not_required')


class PharmaQcResultLine(models.Model):
    """Ties a QC result to the instrument that produced it.

    The instrument's calibration position is copied onto the result when the
    value is entered. Recalibrating the instrument later does not change what
    the result shows. An instrument out of calibration stops the result at
    entry, not at approval: by then the sample is consumed.
    """
    _inherit = 'pharma.qc.result.line'

    instrument_id = fields.Many2one(
        comodel_name='maintenance.equipment',
        domain="[('equipment_class', '=', 'testing')]",
        index='btree_not_null',
        help='Instrument the result was measured on. Proposed from the '
             'specification; any equally qualified instrument may be used.',
    )
    instrument_required = fields.Boolean(
        compute='_compute_instrument_required',
        help='A parameter with a minimum or maximum limit is a measurement and '
             'needs the instrument it was measured on. Qualitative parameters '
             'without limits do not.',
    )
    support_instrument_ids = fields.Many2many(
        comodel_name='maintenance.equipment',
        relation='pharma_result_support_instrument_rel',
        column1='result_line_id',
        column2='equipment_id',
        string='Support Instruments',
        domain="[('equipment_class', '=', 'testing')]",
        help='Other instruments used for the measurement, e.g. a balance '
             'for sample preparation.',
    )
    instrument_calibration_date = fields.Date(
        string='Instrument Calibrated On',
        readonly=True,
        copy=False,
        help='Last passed calibration of the instrument when the value was entered.',
    )
    instrument_calibration_due = fields.Date(
        readonly=True,
        copy=False,
        help='Next calibration date of the instrument when the value was entered.',
    )
    instrument_calibration_ok = fields.Boolean(
        string='Instrument Calibrated',
        readonly=True,
        copy=False,
        help='The instrument was within calibration when the value was entered.',
    )

    @api.depends('expected_min', 'expected_max')
    def _compute_instrument_required(self):
        """A result with a limit is a measurement and needs an instrument."""
        for line in self:
            line.instrument_required = bool(line.expected_min or line.expected_max)

    @api.constrains('instrument_id', 'result_entered', 'expected_min', 'expected_max')
    def _check_instrument_required(self):
        """Refuse an entered measurement that names no instrument."""
        for line in self:
            if line.result_entered and line.instrument_required and not line.instrument_id:
                raise ValidationError(self.env._(
                    'Select the instrument used to measure "%s".',
                    line.parameter or self.env._('this parameter')))

    @api.onchange('parameter_id')
    def _onchange_parameter_id_instrument(self):
        """Propose the specification's default instrument."""
        if self.parameter_id.default_instrument_id and not self.instrument_id:
            self.instrument_id = self.parameter_id.default_instrument_id

    @api.model_create_multi
    def create(self, vals_list):
        """Default the instrument (onchange does not run on code-created lines)."""
        SpecLine = self.env['pharma.qc.spec.line']
        for vals in vals_list:
            if not vals.get('instrument_id') and vals.get('parameter_id'):
                default = SpecLine.browse(vals['parameter_id']).default_instrument_id
                if default:
                    vals['instrument_id'] = default.id
        lines = super().create(vals_list)
        # Lines generated from a specification carry a placeholder value, not
        # a measurement, so they are only checked once a value is written.
        lines.filtered('result_entered')._pharma_snapshot_calibration()
        return lines

    def write(self, vals):
        """Check and snapshot the instrument whenever a value is entered."""
        res = super().write(vals)
        touched = {'actual_value', 'instrument_id', 'support_instrument_ids'}
        if touched & set(vals):
            entered = self.filtered('result_entered')
            entered._pharma_check_instruments()
            entered._pharma_snapshot_calibration()
            entered._pharma_warn_unclean_instruments()
        return res

    def _pharma_unclean_instruments(self):
        """Instruments of the line that need cleaning and are not clean."""
        instruments = (self.instrument_id | self.support_instrument_ids).sudo()
        instruments._pharma_refresh_states()
        return instruments.filtered(
            lambda i: i.cleaning_state in ('dirty', 'in_progress', 'hold_expired', 'dirty_hold_expired'))

    def _pharma_warn_unclean_instruments(self):
        """In warn mode, record on the order that a result was measured on
        an instrument that was not clean."""
        if self.env['maintenance.equipment']._pharma_equipment_settings()['check'] != 'warn':
            return
        for line in self:
            unclean = line._pharma_unclean_instruments()
            if unclean and line.test_order_id:
                states = dict(unclean._fields['cleaning_state'].selection)
                line.test_order_id.message_post(body=self.env._(
                    'Warning: %(param)s was measured on an instrument that was not clean: %(items)s.',
                    param=line.parameter or '?',
                    items=', '.join('%s (%s)' % (i.display_name, states[i.cleaning_state])
                                    for i in unclean)))

    @api.onchange('instrument_id', 'support_instrument_ids')
    def _onchange_instrument_cleaning(self):
        """Warn on picking an instrument that is not clean."""
        unclean = self._pharma_unclean_instruments()
        if unclean:
            states = dict(unclean._fields['cleaning_state'].selection)
            return {'warning': {
                'title': self.env._('Instrument not clean'),
                'message': self.env._('%s: clean it before use.', ', '.join(
                    '%s (%s)' % (i.display_name, states[i.cleaning_state]) for i in unclean)),
            }}

    def _pharma_check_instruments(self):
        """Refuse a value measured on an instrument out of calibration, or
        not clean."""
        if not self:
            return
        mode = self.env['maintenance.equipment']._pharma_equipment_settings()['check']
        if mode != 'block':
            return
        instruments = (self.instrument_id | self.support_instrument_ids).sudo()
        instruments._pharma_refresh_states()
        bad = instruments.filtered(lambda i: i.calibration_state not in CALIBRATION_OK)
        if bad:
            raise ValidationError(self.env._(
                'The result cannot be entered: %s is out of calibration. Use a '
                'calibrated instrument, or have this one calibrated first.',
                ', '.join(bad.mapped('display_name'))))
        unclean = self._pharma_unclean_instruments()
        if unclean:
            raise ValidationError(self.env._(
                'The result cannot be entered: %s is not clean. Clean the '
                'instrument first.',
                ', '.join(unclean.mapped('display_name'))))

    def _pharma_snapshot_calibration(self):
        """Copy the instrument's calibration position onto the result."""
        for line in self:
            instrument = line.instrument_id.sudo()
            instrument._pharma_refresh_states()
            vals = {
                'instrument_calibration_date': instrument.last_calibration_date,
                'instrument_calibration_due': instrument.next_calibration_date,
                'instrument_calibration_ok': (
                    bool(instrument) and instrument.calibration_state in CALIBRATION_OK),
            }
            # None of these fields triggers the checks in write() above.
            line.write(vals)
