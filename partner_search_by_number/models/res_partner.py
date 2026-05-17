# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, models


class ResPartner(models.Model):
    """The ResPartner model is an inherited model of res.partner.
        This model extends the functionality of the res.partner model
        by adding a custom name search method _search_display_name(),
        which searches for partners by their name, phone number,
        or mobile number."""
    _inherit = 'res.partner'

    @api.model
    def _search_display_name(self, operator, value):
        """ The operator and value are passed to the method to build the domain
        dynamically, enabling flexible searching based on the input."""
        domain = ['|', '|', '|', '|', '|',
                  ('complete_name', operator, value),
                  ('email', operator, value), ('ref', operator, value),
                  ('vat', operator, value),
                  ('company_registry', operator, value),
                  ('phone', operator, value)]
        return domain
