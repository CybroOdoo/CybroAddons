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
import logging

from odoo import api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class WmStatusTransitionLog(models.Model):
    """Audit log recording state changes, transition timestamps, and authorizing users."""
    _name = 'wm.status.transition.log'
    _description = 'Status Transition Log'
    _order = 'transition_date desc, id desc'

    model_id = fields.Many2one('ir.model', required=True, index=True, ondelete='cascade')
    res_id = fields.Integer(string='Record ID', required=True, index=True)
    old_state = fields.Char(string='Old Status')
    new_state = fields.Char(string='New Status')
    reason = fields.Char(string='Transition Reason')
    user_id = fields.Many2one('res.users', string='Responsible User', required=True)
    transition_date = fields.Datetime(string='Timestamp', required=True, default=fields.Datetime.now)
    record_name = fields.Char(compute='_compute_record_name')

    @api.depends('model_id', 'res_id')
    def _compute_record_name(self):
        """
        Resolve the display name of the logged source document (collection
        order, contract, etc.) from the reference model and ID, populating the
        human-readable record name column.
        """
        for log in self:
            if log.model_id and log.res_id:
                try:
                    record = self.env[log.model_id.model].browse(log.res_id)
                    if record.exists():
                        log.record_name = record.display_name or f"{log.model_id.name} ({log.res_id})"
                    else:
                        log.record_name = f"{log.model_id.name} ({log.res_id}) [Deleted]"
                except Exception as e:
                    _logger.debug("Failed to resolve record name for %s(%s): %s", log.model_id.model, log.res_id, e)
                    log.record_name = f"{log.model_id.name} ({log.res_id})"
            else:
                log.record_name = "Unknown"

    def write(self, vals):
        """ Block every write: status transition records are immutable. """
        raise exceptions.UserError(self.env._('Audit records cannot be edited by any user, including administrators.'))

    @api.ondelete(at_uninstall=False)
    def _unlink_except_audit_record(self):
        """ Block deletion of status transition records (allowed only at module uninstall). """
        raise exceptions.UserError(self.env._('Audit records cannot be deleted by any user, including administrators.'))
