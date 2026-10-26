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
from odoo.exceptions import UserError


class ComplianceCustody(models.Model):
    """Chain-of-custody transfer event log tracking physical custody transitions."""
    _name = 'wm.compliance.custody'
    _description = 'Chain of Custody'
    _order = 'timestamp asc, id asc'

    manifest_id = fields.Many2one('wm.compliance.manifest', string='Manifest', required=True, ondelete='cascade')
    action = fields.Selection([
        ('generated', 'Generated'),
        ('collected', 'Collected'),
        ('in_transit', 'In Transit'),
        ('received', 'Received'),
        ('disposed', 'Disposed')
    ], string='Action', required=True)
    custodian_id = fields.Many2one('res.users', string='Custodian', default=lambda self: self.env.user, required=True)
    timestamp = fields.Datetime(string='Timestamp', default=fields.Datetime.now, required=True)
    location = fields.Char(string='Location')
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    @api.model_create_multi
    def create(self, vals_list):
        """
        Custody rows belong to their manifest's company, not to the
        company currently selected by the user.
        """
        for vals in vals_list:
            if not self.env.su:
                # Custody evidence cannot be attributed to another user or
                # back/forward-dated by the caller.
                vals['custodian_id'] = self.env.user.id
                vals['timestamp'] = fields.Datetime.now()
            if vals.get('manifest_id'):
                manifest = self.env['wm.compliance.manifest'].browse(vals['manifest_id'])
                if not self.env.su and manifest.state == 'disposed':
                    raise UserError(_("Chain of Custody logs cannot be added to a disposed manifest."))
                if not vals.get('company_id'):
                    vals['company_id'] = manifest.company_id.id
        return super().create(vals_list)

    def write(self, vals):
        """
        Override write to implement business validations and side effects.
        """
        if not (self.env.su and self.env.context.get('bypass_compliance_lock')):
            for rec in self:
                if rec.manifest_id.state != 'draft':
                    raise UserError(_("Chain of Custody logs on active or finalized manifests are legally immutable records and cannot be modified."))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_active_manifest(self):
        """
        Override unlink to handle cascading cleanup or prevent invalid
        deletions.
        """
        if not (self.env.su and self.env.context.get('bypass_compliance_lock')):
            for rec in self:
                if rec.manifest_id.state != 'draft':
                    raise UserError(_("Chain of Custody logs on active or finalized manifests are legally immutable records and cannot be deleted."))
