# -*- coding: utf-8 -*-
#############################################################################
#
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
from odoo import models, fields


class UniversityApplicationType(models.Model):
    """Represents a type of application (e.g. Undergraduate, Graduate) with its
    presentation details, fee, requirements and call-to-action shown on the
    website."""
    _name = 'university.application.type'
    _description = 'University Application Type'
    _order = 'sequence, id'

    name = fields.Char('Name', required=True, translate=True,
                       help='Name of the application type (e.g. Undergraduate, Graduate, Transfer).')
    target_audience = fields.Char('Target Audience', required=True, translate=True,
                                  help='The group of applicants this application type is intended for.')
    description = fields.Text('Description', required=True, translate=True,
                              help='Detailed description of this application type shown to applicants.')
    icon_class = fields.Char('Icon CSS Class', default='bi-mortarboard-fill', required=True,
                             help='CSS class of the icon (e.g. Bootstrap Icons) displayed for this application type.')
    color_bg = fields.Char('Background Color', default='#e8f0fe', required=True,
                           help='Background color of the application type card, as a hex code.')
    color_text = fields.Char('Text Color', default='#1a3a6b', required=True,
                             help='Text color of the application type card, as a hex code.')
    application_fee = fields.Char('Application Fee', default='$75', required=True,
                                  help='Application fee displayed for this application type.')
    requirement_ids = fields.Many2many('university.admission.requirement', 'univ_app_type_req_rel', 'app_type_id', 'req_id', string='Requirements',
                                       help='Admission requirements associated with this application type.')
    cta_text = fields.Char('CTA Button Text', required=True, translate=True,
                           help='Text shown on the call-to-action button for this application type.')
    cta_url = fields.Char('CTA Button URL', default='#how-to-apply', required=True,
                          help='URL or anchor the call-to-action button links to.')
    sequence = fields.Integer('Sequence', default=10,
                              help='Determines the display order of application types. Lower values appear first.')
