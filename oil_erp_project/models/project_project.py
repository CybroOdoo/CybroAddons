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
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class Project(models.Model):
    """
    Extends 'project.project' to support oil and gas industry specific fields
    such as operator details, geological formations, and license tracking.
    """
    _inherit = 'project.project'

    storage_location_id = fields.Many2one(
        'stock.location',
        string='Storage Location',
        readonly=True,
        copy=False,
        help="Select the storage Location.")
    is_oil_gas_project = fields.Boolean(
        string='Is Oil Gas Project',
        help='Enable if it is oil and gas project.')

    # ── Project Classification ──
    project_code = fields.Char(
        string='Project Code',
        help='Official project reference code.')
    operator_id = fields.Many2one(
        'res.partner',
        string='Operator',
        help='Operating company (may differ from the Odoo company).')
    block_number = fields.Char(
        string='Block / License Area',
        help='Concession block or license area number.')
    country_id = fields.Many2one(
        'res.country',
        string='Country',
        help='Country of operation.')
    state_id = fields.Many2one(
        'res.country.state',
        string='State / Province',
        domain="[('country_id', '=?', country_id)]",
        help='State or province within the country of operation.')

    # ── Reservoir & Geology Link ──
    field_name = fields.Char(
        string='Field / Area Name',
        help='Common name of the field or area (e.g. "North Slope Block 3").')
    primary_fluid_type = fields.Selection(
        [
            ('oil', 'Oil'),
            ('gas', 'Gas'),
            ('condensate', 'Condensate'),
        ],
        string='Primary Fluid Type',
        help='Primary fluid produced — mirrors the reservoir fluid type.')
    formation = fields.Char(
        string='Target Formation',
        help='Target geological formation name.')

    # ── Commercial & Contract Info ──
    license_number = fields.Char(
        string='License Number',
        help='Production license or concession number.',
    )
    license_expiry = fields.Date(
        string='License Expiry',
        tracking=True,
        help='License expiry date — triggers alerts when approaching.')
    working_interest = fields.Float(
        string='Working Interest (%)',
        help="Company's working interest percentage.")
    net_revenue_interest = fields.Float(
        string='Net Revenue Interest (%)',
        help='Net revenue interest percentage.')
    contract_type = fields.Selection(
        [
            ('psc', 'Production Sharing Contract'),
            ('concession', 'Concession'),
            ('service_contract', 'Service Contract'),
            ('jv', 'Joint Venture'),
        ],
        string='Contract Type',
        help='Type of contractual arrangement.')
    jv_partner_ids = fields.Many2many(
        'res.partner',
        string='JV Partners',
        help='Joint venture partners in this project.')

    # ── Constraints ──
    @api.constrains('working_interest')
    def _check_working_interest(self):
        """
        Validates that the working interest percentage is between 0 and 100.
        """
        for rec in self:
            if rec.working_interest and (
                    rec.working_interest < 0 or rec.working_interest > 100):
                raise ValidationError(
                    _('Working interest must be between 0 and 100%%.'))

    @api.constrains('net_revenue_interest')
    def _check_net_revenue_interest(self):
        """
        Validates that the net revenue interest percentage is between 0 and 100.
        """
        for rec in self:
            if rec.net_revenue_interest and (
                    rec.net_revenue_interest < 0 or rec.net_revenue_interest > 100):
                raise ValidationError(
                    _('Net revenue interest must be between 0 and 100%%.'))

    @api.onchange('country_id')
    def _onchange_country_id(self):
        """
        Resets the state field if the chosen state does not belong to the selected country.
        """
        if self.state_id and self.state_id.country_id != self.country_id:
            self.state_id = False

    # ── Actions ──
    def action_view_storage_locations(self):
        """
        Navigates to the linked stock location form view.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Storage Location'),
            'res_model': 'stock.location',
            'view_mode': 'form',
            'res_id': self.storage_location_id.id,
            'target': 'current',
        }

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides create to automatically link industry-specific task stages
        and initialize storage locations for new oil and gas projects.
        """
        # Pre-fetch the Oil & Gas stages outside the loop for better performance
        oil_gas_stages = self.env['project.task.type'].search([
            ('is_oil_gas_task_stage', '=', True)
        ])

        # We need to handle the logic before or during creation to include type_ids
        for vals in vals_list:
            if vals.get('is_oil_gas_project') and oil_gas_stages:
                # Use Command.set (equivalent to 6,0) to link the stages
                vals['type_ids'] = [fields.Command.set(oil_gas_stages.ids)]

        # Create the projects
        projects = super().create(vals_list)

        # Post-create: ensure only oil & gas task stages are linked
        for project in projects:
            if project.is_oil_gas_project and oil_gas_stages:
                non_oil_stages = project.type_ids - oil_gas_stages
                if non_oil_stages:
                    project.type_ids = oil_gas_stages

        # Post-create logic for Storage Locations
        for project in projects:
            if project.is_oil_gas_project and not project.storage_location_id:
                location = self.env['stock.location'].create([{
                    'name': f"Storage: {project.name}",
                    'usage': 'internal',
                }])
                project.storage_location_id = location.id

        return projects
