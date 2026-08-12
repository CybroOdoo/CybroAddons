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

from odoo import models
from odoo.exceptions import AccessError


class PharmaWorkflowMixin(models.AbstractModel):
    """Shared permission helper enforcing QA-only access on pharma workflow buttons."""
    _name = 'pharma.workflow.mixin'
    _description = 'Pharma Workflow Permission Helper'

    def _check_pharma_group(self, group_xmlid, message):
        """Raise ``AccessError`` when the current user is not in ``group_xmlid``."""
        if not self.env.user.has_group(group_xmlid):
            raise AccessError(message)
