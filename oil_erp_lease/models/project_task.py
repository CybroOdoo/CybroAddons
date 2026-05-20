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


class ProjectTask(models.Model):
    """Extends project.task to show a lease expiry warning inherited
    from the parent project's lease agreement."""
    _inherit = 'project.task'

    lease_expiry_warning = fields.Text(
        string='Lease Expiry Warning',
        compute='_compute_lease_expiry_warning',
        help="Warning if the project's lease agreement has expired.")

    def _compute_lease_expiry_warning(self):
        """Shows warning if the parent project's lease has expired."""
        for record in self:
            lease = record.project_id.lease_id if record.project_id else False
            if lease and lease.state == 'expired':
                record.lease_expiry_warning = _(
                    "Lease Agreement '%s' linked to project '%s' has "
                    "expired.", lease.name, record.project_id.name)
            else:
                record.lease_expiry_warning = False