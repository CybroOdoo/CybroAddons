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
#############################################################################
from odoo import fields, models


class DripMailingHistory(models.Model):
    """Drip mail sent to a contact of a mailing list."""
    _name = 'drip.mailing.history'
    _description = 'Drip Mailing History'
    _order = 'send_date desc, id desc'

    name = fields.Char(help="Name of the drip")
    contact_id = fields.Many2one(
        'mailing.contact', ondelete='cascade',
        help="Contact the drip was sent to")
    mailing_id = fields.Many2one(
        'mailing.list', string="Mailing List", ondelete='cascade',
        help="Mailing list of the drip")
    template_id = fields.Many2one(
        'drip.template', string="Drip Template", ondelete='set null',
        help="Template of the drip")
    send_date = fields.Date(help="Date the drip was sent")
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
        help="Company of the drip")
