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
from odoo import fields, models


class ResPartner(models.Model):
    """Extends Partner with waste management classification, licences, and compliance status."""
    _inherit = 'res.partner'

    is_generator = fields.Boolean(
        string='Is Generator',
        compute='_compute_is_generator',
        store=True,
        readonly=False,
        precompute=True,
        help='Automatically set if the partner has waste contracts or collection orders.'
    )
    is_transporter = fields.Boolean(
        string='Is Transporter',
        default=False,
        help='Mark this partner as a waste transporter/carrier.'
    )
    is_driver = fields.Boolean(string='Is Driver', help='Mark this contact as a waste collection driver.')
    licence_expiry = fields.Date(string='Licence Expiry Date', help='Driver licence expiry date.')

    def _compute_is_generator(self):
        """Compute base default generator status for partner records."""
        for partner in self:
            partner.is_generator = False
