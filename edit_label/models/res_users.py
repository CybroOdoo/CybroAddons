# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Mruthul Raj (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models


class ResUser(models.Model):
    """Extends the 'res.users' model to include an 'is_edit_field_label'
    field."""
    _inherit = 'res.users'

    is_edit_field_label = fields.Boolean(string='Edit Field Label',
                                         help="Allows the user to edit field "
                                              "labels.")

    @api.model
    def login_user(self):
        """Retrieves the 'is_edit_field_label' value for the current user
        upon login.
        Returns:True if the user can edit field labels, False otherwise."""
        user = self.env.user
        return user.is_edit_field_label
