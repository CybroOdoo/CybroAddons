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

from odoo import fields, models
from odoo.tools.translate import _


class ProjectProject(models.Model):
    """Extends project.project to link with a lease agreement and
    show an expiry warning when the lease has expired."""
    _inherit = 'project.project'

    lease_id = fields.Many2one(
        'oil.lease.agreement',
        string='Lease Agreement',
        domain="[('state', '=', 'active')]",
        tracking=True,
        help="Lease agreement this project operates under.")
    lease_expiry_warning = fields.Text(
        string='Lease Expiry Warning',
        compute='_compute_lease_expiry_warning',
        help="Warning if the related lease agreement has expired.")

    def _compute_lease_expiry_warning(self):
        """Shows warning if the lease agreement has expired."""
        for record in self:
            if record.lease_id and record.lease_id.state == 'expired':
                record.lease_expiry_warning = _(
                    "Lease Agreement '%s' has expired. All related "
                    "operations should be reviewed.",
                    record.lease_id.name)
            else:
                record.lease_expiry_warning = False