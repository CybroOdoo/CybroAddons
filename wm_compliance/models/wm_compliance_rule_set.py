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


class WmComplianceRuleSet(models.Model):
    """Configurable Compliance Rule Set matching regions, waste streams, and regulatory requirements."""
    _name = 'wm.compliance.rule.set'
    _description = 'Configurable Compliance Rule Set'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'wm.audit.mixin']
    _order = 'sequence asc, id desc'

    LOCKED_STATES = ['locked']

    name = fields.Char(string='Rule Set Name', required=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    country_id = fields.Many2one('res.country', string='Country', help='Leave empty to apply to all countries', tracking=True)
    state_id = fields.Many2one('res.country.state', string='State / Region', help='Leave empty to apply to all states/regions', tracking=True)
    waste_category_id = fields.Many2one('wm.waste.category', string='Waste Category', help='Leave empty to apply to all waste categories', tracking=True)
    manifest_type = fields.Selection([
        ('hazardous', 'Hazardous'),
        ('non_hazardous', 'Non-Hazardous'),
        ('medical', 'Medical'),
    ], string='Manifest Type', help='Optional finer match on waste stream type', tracking=True)
    requires_manifest = fields.Boolean(string='Requires Manifest', default=True, tracking=True)
    required_code_ids = fields.Many2many(
        'wm.compliance.code',
        'wm_compliance_rule_set_code_rel',
        'rule_set_id',
        'code_id',
        string='Required Compliance Codes',
        tracking=True
    )
    retention_years = fields.Integer(string='Retention Period (Years)', default=5, help='Minimum years these records must be retained for this region/stream', tracking=True)
    effective_date = fields.Date(string='Effective Date', default=fields.Date.context_today, required=True, tracking=True)
    expiry_date = fields.Date(string='Expiry Date', tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('locked', 'Locked / Archived')
    ], string='Status', default='draft', required=True, tracking=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.model
    def _get_applicable_rules(self, collection_point=None, waste_category=None, manifest_type=None, date=None, country=None, state=None):
        """
        Find and return matching wm.compliance.rule.set records ordered by specificity.
        Resolution precedence:
        Matches with State + Waste Category > Country + Waste Category > State-only > Country-only > Global fallback.
        A falsy ``manifest_type`` means the caller does not know the stream
        type, so rules of any manifest type remain candidates.
        """
        date = date or fields.Date.today()
        domain = [
            ('active', '=', True),
            # Draft rule sets are still being written: never enforce them
            ('state', '!=', 'draft'),
            ('effective_date', '<=', date),
            '|', ('expiry_date', '=', False), ('expiry_date', '>=', date),
        ]
        candidates = self.search(domain, order='sequence asc')

        c_state = state or (collection_point.state_id if collection_point else False)
        c_country = country or (collection_point.country_id if collection_point else False)

        matches = candidates.filtered(lambda r:
            (not r.state_id or r.state_id == c_state) and
            (not r.country_id or r.country_id == c_country) and
            (not r.waste_category_id or r.waste_category_id == waste_category) and
            (not r.manifest_type or not manifest_type or r.manifest_type == manifest_type)
        )

        return matches.sorted(key=lambda r: (
            (1 if r.waste_category_id else 0) * 8 +
            (1 if r.manifest_type else 0) * 4 +
            (1 if r.state_id else 0) * 2 +
            (1 if r.country_id else 0)
        ), reverse=True)

    def write(self, vals):
        """A locked rule set stays immutable, except that it can be archived
        (retired) so it stops being offered."""
        if vals and set(vals) <= {'active'}:
            self.check_access('write')
            return super(WmComplianceRuleSet, self.sudo().with_context(bypass_compliance_lock=True)).write(vals)
        return super().write(vals)

    def action_activate(self):
        """Publish a draft rule set so it is enforced."""
        self.filtered(lambda r: r.state == 'draft').write({'state': 'active'})

    def action_lock(self):
        """Lock rule set once used by historical records."""
        for rec in self:
            rec.write({'state': 'locked'})
