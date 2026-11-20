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


class HospitalWard(models.Model):
    """Class holding Ward details"""
    _name = 'hospital.ward'
    _description = 'Hospital Ward'
    _rec_name = 'ward_no'

    ward_no = fields.Char(string="Name",
                          required=True, help='Number of the ward')
    building_id = fields.Many2one('hospital.building',
                                  string="Block", help='The building to '
                                                       'which the ward '
                                                       'corresponds to')
    floor_no = fields.Integer(string="Floor No.", help='The floor to '
                                                       'which the ward '
                                                       'corresponds to')
    note = fields.Text(help='Note regarding the ward')
    bed_count = fields.Integer(string="Count", compute="_compute_bed_count",
                               help='The bed count')
    nurse_ids = fields.Many2many('hr.employee',
                                 domain="[('job_id.name','=','Nurse')]",
                                 help='Nurses corresponds to the ward')
    ward_facilities_ids = fields.Many2many('room.facility',
                                           string='Facilities',
                                           help='Facilities corresponds to '
                                                'ward.')
    _name_uniq = models.Constraint(
        'unique (ward_no)',
        "Ward number should be unique!",
    )

    def _compute_bed_count(self):
        """Method for computing bed count"""
        for rec in self:
            rec.bed_count = rec.env['hospital.bed'].sudo().search_count([(
                'ward_id', '=', rec.id)])

    def action_get_open_bed(self):
        """Returns form view of bed"""
        return {
            'name': 'Bed',
            'domain': [('ward_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.bed',
            'view_mode': 'list',
            'context': {'create': False},
        }

    @api.model
    def fetch_ward_details(self):
        """Function for fetch ward details"""
        return self.sudo().search_read()
