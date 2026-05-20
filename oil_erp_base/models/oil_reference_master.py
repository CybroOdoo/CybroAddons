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


class OilReferenceMaster(models.Model):
    _name = 'oil.reference.master'
    _description = 'Oil Reference Master'
    _rec_name = 'name'
    _order = 'reference_type, sequence, name, id'

    name = fields.Char(required=True,
                       help="Display name of the reference entry used across the Oil ERP system.")
    code = fields.Char(required=True,
                       help="Short unique code identifying this reference entry.")
    reference_type = fields.Selection(
        [
            ('primary_fluid_type', 'Primary Fluid Type'),
            ('well_type', 'Well Type'),
            ('transfer_product_type', 'Transfer Product Type'),
            ('incident_type', 'Incident Type'),
        ],
        required=True,
        help="Category this reference belongs to, determining where it can be used.",
    )
    sequence = fields.Integer(default=10,
                              help="Order in which this entry appears in dropdowns and lists.")
    active = fields.Boolean(default=True,
                            help="Uncheck to archive this entry without deleting it.")
