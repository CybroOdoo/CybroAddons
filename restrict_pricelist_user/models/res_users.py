# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amaya Aravind (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class ResUsers(models.Model):
    """ Class for the inherited model res_users. Contains fields for choosing
        pricelists, restrict pricelists and a compute method of is_restricted
        field. """
    _inherit = 'res.users'

    pricelist_ids = fields.Many2many('product.pricelist',
                                     'rel_user_pricelist',
                                     help='Choose the allowed pricelists for '
                                          'the user', string="Price Lists")
    is_restricted = fields.Boolean(help='Restrict pricelists for the user',
                                   string="Restricted",
                                   compute="_compute_is_restricted")

    def _compute_is_restricted(self):
        """Compute method of is_restricted field. Computes the field according
            to the field in res_config_settings."""
        pricelist_restricted = self.env['ir.config_parameter'].sudo().\
            get_param('restrict_pricelist_user.is_restricted')
        for rec in self:
            rec.is_restricted = True if pricelist_restricted else False
