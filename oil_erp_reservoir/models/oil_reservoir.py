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
from odoo.orm.table_objects import Constraint
from odoo.tools.translate import _
from odoo.exceptions import ValidationError



class OilReservoir(models.Model):
    """
    Manages underground oil and gas reservoirs, tracking geological data 
    (formation, porosity, permeability) and estimated reserves. Automatically 
    creates associated projects for exploration and production.
    """
    _name = 'oil.reservoir'
    _description = 'Oil Reservoir Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name_unique = Constraint(
        'UNIQUE(name, company_id)',
        'The Reservoir Name must be unique per company!'
    )
    _code_unique = Constraint(
        'UNIQUE(code, company_id)',
        'The Reservoir Code must be unique per company!'
    )


    def _get_default_stage_id(self):
        """ Gives default stage_id """
        return self.env.ref('oil_erp_reservoir.project_stage_exploration').id

    name = fields.Char(string='Reservoir Name', required=True, tracking=True,
                       help="Name identifying this underground reservoir.")
    code = fields.Char(string='Reference/Code', copy=False, tracking=True,
                       help="Short unique reference code for this reservoir.")
    location = fields.Char(string='Geographical Location',
                           help="Geographical location or area description.")

    # Geological Info
    formation = fields.Char(string='Geological Formation',
                            help="Target geological formation containing the reservoir.")
    depth_ft = fields.Float(string='Depth (ft)', tracking=True,
                            help="Total measured depth of the reservoir in feet.")
    porosity = fields.Float(string='Porosity (%)',
                            help="Percentage of void space in the rock.")
    permeability = fields.Float(string='Permeability (mD)',
                                help="Ability of the rock to transmit fluids.")
    fluid_type_id = fields.Many2one(
        'oil.reference.master',
        string='Primary Fluid Type',
        domain="[('reference_type', '=', 'primary_fluid_type')]",
        tracking=True,
        help="Primary fluid type produced from this reservoir.")

    # Reserves Estimation
    estimated_reserves = fields.Float(string='Estimated Reserves (MMboe)',
                                      tracking=True,
                                      help="Millions of Barrels of Oil Equivalent")
    recovery_factor = fields.Float(string='Recovery Factor (%)',
                                   help="Expected percentage of reserves that can be economically recovered.")

    # Status
    stage_id = fields.Many2one(
        'project.project.stage',
        string='Stage',
        tracking=True,
        domain="[('is_oil_project_stage', '=', True)]",
        default=lambda self: self._get_default_stage_id(),
        copy=False,
        help="Current lifecycle stage of this reservoir.")
    project_id = fields.Many2one('project.project', string='Project',
                                 readonly=True, copy=False,
                                 help="Upstream project automatically created for this reservoir.")
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True,
        tracking=True,
        help="Warehouse owning the storage location of the auto-created project. "
             "Passed through to the project's storage location as its parent.")

    notes = fields.Text(string='Geological Notes',
                        help="Geological notes, observations, and technical remarks.")
    active = fields.Boolean(default=True,
                            help="Uncheck to archive this reservoir without deleting it.")
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        help="Company that owns this reservoir record.")
    task_ids = fields.One2many('project.task', related='project_id.task_ids',
                               help="Well tasks linked to this reservoir project.")
    task_count = fields.Integer(string='Tasks Count',
                                compute='_compute_task_count',
                                help="Number of well tasks in this reservoir project.")

    def init(self):
        self.env.cr.execute("""
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'oil_reservoir'
              AND column_name = 'fluid_type'
        """)
        if self.env.cr.fetchone():
            self.env.cr.execute("""
                UPDATE oil_reservoir reservoir
                SET fluid_type_id = ref.id
                FROM oil_reference_master ref
                WHERE reservoir.fluid_type_id IS NULL
                  AND reservoir.fluid_type = ref.code
                  AND ref.reference_type = 'primary_fluid_type'
            """)

    @api.constrains('depth_ft', 'porosity', 'permeability', 'recovery_factor')
    def _check_geology_values(self):
        """
        Validates geological measurements:
        - Depth, porosity, permeability, and recovery factor must be non-negative.
        - Porosity and recovery factor must be <= 100%.
        """
        for rec in self:
            if rec.depth_ft < 0:
                raise ValidationError(_("Depth cannot be negative."))
            if rec.porosity < 0 or rec.porosity > 100:
                raise ValidationError(_("Porosity must be between 0 and 100%."))
            if rec.permeability < 0:
                raise ValidationError(_("Permeability cannot be negative."))
            if rec.recovery_factor < 0 or rec.recovery_factor > 100:
                raise ValidationError(
                    _("Recovery Factor must be between 0 and 100%."))

    @api.constrains('name', 'code', 'company_id')
    def _check_uniqueness(self):
        """
        Python-level uniqueness fallback for reservoir name and code.
        """
        for rec in self:
            if rec.name:
                domain = [('name', '=', rec.name), ('id', '!=', rec.id),
                          ('company_id', '=', rec.company_id.id)]
                if self.search_count(domain) > 0:
                    raise ValidationError(
                        _("The Reservoir Name '%s' must be unique per company!",
                          rec.name))
            if rec.code:
                domain = [('code', '=', rec.code), ('id', '!=', rec.id),
                          ('company_id', '=', rec.company_id.id)]
                if self.search_count(domain) > 0:
                    raise ValidationError(
                        _("The Reservoir Code '%s' must be unique per company!",
                          rec.code))

    @api.depends('task_ids')
    def _compute_task_count(self):
        """
        Computes the number of tasks linked to the reservoir's associated project.
        """
        for record in self:
            record.task_count = len(record.task_ids)

    def action_view_tasks(self):
        """
        Returns an action to open a list view of all tasks linked to this reservoir.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tasks',
            'view_mode': 'list,form',
            'res_model': 'project.task',
            'domain': [('id', 'in', self.task_ids.ids)],
            'context': {'default_project_id': self.project_id.id},
        }

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides create to automatically generate a corresponding upstream 
        project for each new reservoir.
        """
        reservoirs = super().create(vals_list)
        for reservoir in reservoirs:
            if not reservoir.project_id:
                project_vals = {
                    'name': f"Project: {reservoir.name}",
                    'is_oil_gas_project': True,
                    'description': f"Auto-created project for Reservoir {reservoir.name}",
                    'reservoir_id': reservoir.id,
                    'warehouse_id': reservoir.warehouse_id.id,
                    'primary_fluid_type_id': reservoir.fluid_type_id.id,
                }
                if reservoir.stage_id:
                    project_vals['stage_id'] = reservoir.stage_id.id

                project = self.env['project.project'].create([project_vals])
                reservoir.write({'project_id': project.id})
        return reservoirs

    def write(self, vals):
        """
        Overrides write to synchronize the reservoir's stage with its linked 
        upstream project.
        """
        res = super().write(vals)
        if 'stage_id' in vals or 'fluid_type_id' in vals:
            for record in self:
                if record.project_id and record.project_id.stage_id != record.stage_id:
                    record.project_id.stage_id = record.stage_id.id
                if record.project_id and record.project_id.primary_fluid_type_id != record.fluid_type_id:
                    record.project_id.primary_fluid_type_id = record.fluid_type_id.id
        return res
