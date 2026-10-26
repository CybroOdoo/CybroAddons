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
from odoo import _, api, fields, models


class WmEventPricingRule(models.Model):
    """Rate table mirroring wm.pricing.rule, keyed by event type instead of category."""
    _name = 'wm.event.pricing.rule'
    _description = 'Billable Event Pricing Rule'
    _order = 'sequence asc, id desc'

    name = fields.Char(string='Rule Name', default=lambda self: _('New'), required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    event_type = fields.Selection([
        ('extra_pickup', 'Extra Pickup'),
        ('overweight', 'Overweight Load'),
        ('contamination', 'Contaminated Load'),
        ('emergency_callout', 'Emergency Callout'),
    ], string='Event Type', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', help='Leave empty for All Customers')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    price_unit = fields.Float(string='Unit Price', default=0.0, help='Flat fee, or per-kg rate for overweight')
    min_charge = fields.Float(string='Minimum Charge', default=0.0)
    effective_date = fields.Date(string='Effective Date', default=fields.Date.context_today, required=True)
    expiry_date = fields.Date(string='Expiry Date')
    active = fields.Boolean(string='Active', default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('New'):
                event_label = dict(self._fields['event_type'].selection).get(vals.get('event_type'), '')
                if vals.get('partner_id'):
                    partner = self.env['res.partner'].browse(vals['partner_id'])
                    vals['name'] = _("%(type)s Rule - %(partner)s") % {
                        'type': event_label, 'partner': partner.name}
                else:
                    vals['name'] = _("%s Rule") % event_label
        return super().create(vals_list)
