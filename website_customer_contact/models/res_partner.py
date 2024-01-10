# -- coding: utf-8 --
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, models


class ResPartner(models.Model):
    """ Model for extending res.partner to compute display name."""
    _inherit = 'res.partner'

    @api.depends('is_company', 'name', 'parent_id.display_name', 'type',
                 'company_name')
    def _compute_display_name(self):
        """ Compute the display name for each partner."""
        names = dict(self.with_context({}).name_get())
        for partner in self:
            if partner.website_id:
                partner.display_name = partner.name
            else:
                partner.display_name = names.get(partner.id)
