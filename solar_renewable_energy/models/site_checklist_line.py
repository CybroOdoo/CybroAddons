# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amrithesh K (odoo@cybrosys.com)
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

class SiteChecklistLine(models.Model):
    """Class for site checklist lines"""
    _name = 'site.checklist.line'
    _description = 'Site Checklist Line'

    site_checklist_id = fields.Many2one(
        'site.inspection',
        string="Site Inspection",
        help="The site inspection to which this line belongs.")
    sequence = fields.Integer(
        string="Sequence",
        help="The order of the checklist line. Use the handle to reorder.")
    name = fields.Char(
        string="Checklist Item",
        required=True,
        help="Description of the checklist item that needs to be checked.")
    is_checked = fields.Boolean(
        string="Checked",
        help="Indicates whether this checklist item has been checked/completed.")
    description = fields.Text(
        string="Description",
        help="Additional details or instructions related to this checklist item.")