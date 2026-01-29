# -- coding: utf-8 --
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, models


class ResPartner(models.Model):
    """ Model for extending res.partner to compute display name """
    _inherit = 'res.partner'

    @api.depends('is_company', 'name', 'parent_id.display_name', 'type',
                 'company_name')
    def _compute_display_name(self):
        """ Compute the display name for each partner """
        names = dict(self.with_context({}).name_get())
        for partner in self:
            if partner.website_id:
                partner.display_name = partner.name
            else:
                partner.display_name = names.get(partner.id)
