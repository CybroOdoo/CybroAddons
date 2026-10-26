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
from odoo import api, fields, models


class ResPartner(models.Model):
    """Extends Partner with waste management roles (generator, transporter, driver) and driver licence expiry."""
    _inherit = 'res.partner'

    is_generator = fields.Boolean(
        compute='_compute_is_generator',
        store=True,
        readonly=False,
        precompute=True,
        help='Automatically set if the partner has waste contracts or collection orders.'
    )
    is_transporter = fields.Boolean(
        default=False,
        help='Mark this partner as a waste transporter/carrier.'
    )
    is_driver = fields.Boolean(help='Mark this contact as a waste collection driver.')
    licence_expiry = fields.Date(string='Licence Expiry Date', help='Driver licence expiry date.')

    @api.depends('is_company')
    def _compute_is_generator(self):
        """Base default: not a generator. wm_contracts_billing refines this from contracts and orders."""
        for partner in self:
            partner.is_generator = False
