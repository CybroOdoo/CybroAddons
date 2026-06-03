# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Shalfa P (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class NomineeRelation(models.Model):
    """
    Model representing a nominee relation record within the system.

    This model is used to define and store various types of relationships
    between a nominee and an insured entity, such as "spouse," "child,"
    or "parent." Each relation must have a unique name for identification
    and categorization purposes.

    """

    _name = 'nominee.relation'
    _description = "Nominee Relation"

    name = fields.Char(
        string="Name",
        required=True,
        help="The name of the nominee relation. This should be unique for each relation."
    )

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "This nominee relation already exists!"),
    ]
