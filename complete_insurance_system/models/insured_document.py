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


class InsuredDocument(models.Model):
    """
    Model representing an insured document record within the system.

    This model is used to store and manage documents associated with insured entities.
    Each document has a unique name, which helps in identifying and categorizing
    it, and a color tag which can be used in the UI for quick visual reference.

    """

    _name = 'insured.document'
    _description = "Insured Document"

    name = fields.Char(
        string="Name",
        required=True,
        help="The name of the insured document. This should be unique for each document."
    )
    color = fields.Integer(
        string='Color',
        help="Color code to display as a tag for the document."
    )

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "This insured document already exists!"),
    ]
