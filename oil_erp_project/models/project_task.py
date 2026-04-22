# -*- coding: utf-8 -*-
#############################################################################
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
import logging

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    """
    Extends 'project.task' to represent oil and gas wells. Tracks well identity, 
    GPS coordinates, drilling technical data, and regulatory compliance.
    """
    _inherit = 'project.task'

    is_production_stage = fields.Boolean(
        related='stage_id.is_production',
        help="Enable this when is production stage applies.")

    # ── Well Identity & Classification ──
    is_oil_gas_well = fields.Boolean(
        string='Is Oil and Gas Well',
        related='project_id.is_oil_gas_project',
        store=True,
        readonly=False,
        help='Inherited from project. Enable if this task represents an oil and gas well.')
    well_api_number = fields.Char(
        string='API / UWI Number',
        help='Official well identifier (e.g. 42-123-00001-00-00).')
    well_type = fields.Selection(
        [
            ('oil', 'Oil'),
            ('gas', 'Gas'),
            ('water_injection', 'Water Injection'),
            ('disposal', 'Disposal'),
            ('observation', 'Observation'),
            ('dry', 'Dry'),
        ],
        string='Well Type',
        tracking=True,
        help='Primary purpose of the well.')
    operator_id = fields.Many2one(
        'res.partner',
        string='Operator',
        help='Operating company responsible for the well.')
    field_name = fields.Char(
        string='Field / Area',
        help='Name of the oil/gas field or geographic area.')

    # ── Location & GPS ──
    latitude = fields.Float(
        string='Latitude',
        digits=(10, 6),
        help='GPS latitude of the well location.')
    longitude = fields.Float(
        string='Longitude',
        digits=(10, 6),
        help='GPS longitude of the well location.')
    state_id = fields.Many2one(
        'res.country.state',
        string='State / Province',
        help='Regulatory jurisdiction where the well is located.')
    country_id = fields.Many2one("res.country",
        string='Country',
        help='Country or district of the well location.')

    # ── Drilling & Technical Data ──
    spud_date = fields.Date(
        string='Spud Date',
        tracking=True,
        help='Date when drilling operations began.')
    completion_date = fields.Date(
        string='Completion Date',
        tracking=True,
        help='Date when the well was completed and ready for production.')
    total_depth_ft = fields.Float(
        string='Total Depth (ft)',
        help='Total measured depth drilled in feet.')
    true_vertical_depth_ft = fields.Float(
        string='True Vertical Depth (ft)',
        help='True vertical depth for deviated or horizontal wells.')
    formation = fields.Char(
        string='Target Formation',
        help='Target geological formation for the well.')
    well_direction = fields.Selection(
        [
            ('vertical', 'Vertical'),
            ('directional', 'Directional'),
            ('horizontal', 'Horizontal'),
        ],
        string='Well Direction',
        help='Drilling trajectory type.')

    # ── Regulatory & Compliance ──
    permit_number = fields.Char(
        string='Drilling Permit Number',
        help='Permit number issued by the regulatory authority.')
    permit_date = fields.Date(
        string='Permit Date',
        help='Date the drilling permit was issued.')
    regulatory_id = fields.Char(
        string='Regulatory ID',
        help='State or federal regulatory identification number.')
    maasp_psi = fields.Float(
        string='MAASP (PSI)',
        help='Maximum Allowable Annular Surface Pressure in PSI.')

    # ── Constraints ──
    @api.constrains('spud_date', 'completion_date')
    def _check_well_dates(self):
        """
        Ensures completion date is not before the spud (start of drilling) date.
        """
        for rec in self:
            if rec.spud_date and rec.completion_date and rec.completion_date < rec.spud_date:
                raise ValidationError(
                    _('Completion date cannot be earlier than spud date.'))

    @api.constrains('total_depth_ft', 'true_vertical_depth_ft')
    def _check_depths(self):
        """
        Validates well depth measurements for logical consistency.
        """
        for rec in self:
            if rec.total_depth_ft and rec.total_depth_ft < 0:
                raise ValidationError(_('Total depth cannot be negative.'))
            if rec.true_vertical_depth_ft and rec.true_vertical_depth_ft < 0:
                raise ValidationError(
                    _('True vertical depth cannot be negative.'))
            if (rec.total_depth_ft and rec.true_vertical_depth_ft
                    and rec.true_vertical_depth_ft > rec.total_depth_ft):
                raise ValidationError(
                    _('True vertical depth cannot exceed total depth.'))

    @api.constrains('maasp_psi')
    def _check_maasp(self):
        """
        Validates that Maximum Allowable Annular Surface Pressure is non-negative.
        """
        for rec in self:
            if rec.maasp_psi and rec.maasp_psi < 0:
                raise ValidationError(_('MAASP cannot be negative.'))

    def action_open_production_wizard(self):
        """
        Opens a wizard to record daily production data for this specific well.
        """
        self.ensure_one()
        return {
            'name': _('Record Production'),
            'type': 'ir.actions.act_window',
            'res_model': 'production.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'default_task_id': self.id,
            },
        }

    @api.model
    def cron_check_task_expiry(self):
        """
        Scheduled task to identify and log overdue open tasks.
        """
        today = fields.Date.today()
        expired_tasks = self.search([
            ('date_deadline', '!=', False),
            ('date_deadline', '<', today),
            ('stage_id.fold', '=', False),
        ])
        if expired_tasks:
            _logger.info(
                "Task expiry cron found %s overdue open task(s): %s",
                len(expired_tasks),
                ", ".join(expired_tasks.mapped('display_name')),
            )
        return True
