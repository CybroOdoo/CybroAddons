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
from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class ProjectTask(models.Model):
    """Customize access for project task records."""
    _inherit = 'project.task'

    task_access_user_ids = fields.Many2many('res.users',
                                            string='Access Limited Users',
                                            help="Users who have access "
                                            "to this record")
    is_internal_user = fields.Boolean(string='Is Internal User',
                                      compute='_compute_is_internal_user',
                                      help="Check whether the user is an Internal"
                                      " user or not")

    def _compute_is_internal_user(self):
        """Determines if the current user is an admin to allow the
        'task_access_user_ids' field to be editable only by 'user_admin'."""
        admin = self.env.ref('base.user_admin', raise_if_not_found=False)
        for rec in self:
            rec.is_internal_user = bool(
                rec.env.is_admin() or (admin and rec.env.user.id == admin.id)
            )

    def _check_access_user_modification(self):
        """Ensure only administrators can modify access-limited users."""
        admin = self.env.ref('base.user_admin', raise_if_not_found=False)
        if not (self.env.is_admin() or (admin and self.env.user.id == admin.id)):
            raise AccessError(_("Only administrators are allowed to modify the access list."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('task_access_user_ids'):
                self._check_access_user_modification()
                break
        return super().create(vals_list)

    def write(self, vals):
        if 'task_access_user_ids' in vals:
            self._check_access_user_modification()
        return super().write(vals)
