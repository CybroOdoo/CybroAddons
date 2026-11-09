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
#############################################################################
from odoo import api, fields, models


class ProjectProject(models.Model):
    """Add sequence fields to display unique sequence numbers, project sequence prefix,
    and task sequence references."""

    _inherit = 'project.project'

    project_prefix = fields.Char(
        string='Prefix',
        help='Specify the prefix of the project.',
    )

    task_sequence_id = fields.Many2one(
        'ir.sequence',
        string='Task Entry Sequence',
        help='Create a task entry sequence for each project.',
    )

    project_sequence = fields.Char(
        readonly=True,
        copy=False,
        default='New',
        help='Unique sequence number of the project.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            prefix = vals.get('project_prefix')
            seq = self.env['ir.sequence'].search(
                [('code', '=', 'project.project')],
                limit=1,
            )
            if prefix:
                # If project has a custom prefix
                if seq:
                    seq.prefix = f"{prefix}/"
                else:
                    seq = self.env['ir.sequence'].create({
                        'name': 'Project Project',
                        'implementation': 'standard',
                        'code': 'project.project',
                        'prefix': f"{prefix}/",
                    })
            else:
                # No prefix provided -- use default
                if seq:
                    seq.prefix = 'PRJ/'

            task_seq = self.env['ir.sequence'].create({
                'name': f"Task {vals.get('name', '')}",
                'implementation': 'standard',
            })

            vals['task_sequence_id'] = task_seq.id
            vals['project_sequence'] = self.env[
                'ir.sequence'
            ].next_by_code('project.project')

        return super().create(vals_list)

    def write(self, vals):
        """Update the sequence prefix and regenerate project sequence when prefix changes."""
        if vals.get('project_prefix'):
            sequence = self.env['ir.sequence'].search(
                [('code', '=', 'project.project')],
                limit=1,
            )

            if sequence:
                sequence.prefix = f"{vals['project_prefix']}/"
                vals['project_sequence'] = self.env[
                    'ir.sequence'
                ].next_by_code('project.project')

        return super().write(vals)
