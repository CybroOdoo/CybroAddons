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


class DisposalFacility(models.Model):
    """Registered disposal or processing facility with type, licence/permit details and contact information."""
    _name = 'wm.disposal.facility'
    _description = 'Disposal / Treatment Facility'
    _order = 'name'

    name = fields.Char(string='Facility Name', required=True)
    facility_type = fields.Selection([
        ('landfill', 'Landfill'),
        ('incineration', 'Incineration'),
        ('recycling', 'Recycling'),
        ('composting', 'Composting'),
        ('treatment', 'Treatment'),
        ('other', 'Other')
    ], required=True, default='treatment')
    license_no = fields.Char(string='License / Permit Number')
    license_authority = fields.Char(help="The regulator that issued this license.")
    address = fields.Char()
    contact_email = fields.Char()
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company
    )
