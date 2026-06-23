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
import logging
import threading

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

ALLOWED_TRANSITIONS = {
    'draft': ['under_review'],
    'under_review': ['active'],
    'active': ['special_measures', 'suspended', 'merging', 'dissolved'],
    'special_measures': ['active', 'suspended', 'merging', 'dissolved'],
    'suspended': ['active', 'special_measures', 'merging', 'dissolved'],
    'merging': ['dissolved'],
    'dissolved': [],
}


class NhsOdsSyncRun(models.Model):
    """Track background sync process, audit counts, status, and error logs."""
    _name = 'nhs.ods.sync.run'
    _inherit = ['mail.thread']
    _description = 'ODS sync run history'
    _order = 'started_at desc'
    _rec_name = 'display_name'

    name = fields.Char(
        string='Reference',
        required=True,
        default='New',
        copy=False,
        help="Auto-generated identifier e.g. 'SYNC/2025/00042'.",
    )
    run_type = fields.Selection([
        ('full', 'Full Sync'),
        ('incremental', 'Incremental Delta'),
        ('targeted', 'Targeted (single org)'),
        ('dry_run', 'Dry Run'),
    ], string='Sync Type', required=True, default='incremental', tracking=True)
    triggered_by = fields.Selection([
        ('manual', 'Manual'),
        ('cron', 'Scheduled Cron'),
    ], string='Triggered By', required=True, default='manual',
        help="Sync initiator (e.g. user, cron).",
    )
    user_id = fields.Many2one(
        'res.users',
        string='Triggered By User',
        required=True,
        default=lambda self: self.env.user,
        help="User who triggered this sync run.",
    )
    state = fields.Selection([
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('partial', 'Partial (with errors)'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], string='State', required=True, default='pending', tracking=True,
        help="Current execution state of the sync run.",
    )
    started_at = fields.Datetime(
        string='Started At',
        tracking=True,
        help="Timestamp when the sync execution began.",
    )
    completed_at = fields.Datetime(
        string='Completed At',
        help="Timestamp when the sync execution finished.",
    )
    duration = fields.Float(
        string='Duration (min)',
        compute='_compute_duration',
        help="Minutes between started_at and completed_at.",
    )
    fetched_count = fields.Integer(
        string='Fetched',
        default=0,
        help="Total number of organization stubs fetched from the API.",
    )
    created_count = fields.Integer(
        string='Created',
        default=0,
        help="Number of new trusts created during this run.",
    )
    updated_count = fields.Integer(
        string='Updated',
        default=0,
        help="Number of trusts updated during this run.",
    )
    unchanged_count = fields.Integer(
        string='Unchanged',
        default=0,
        help="Number of trusts that were already up-to-date.",
    )
    conflict_count = fields.Integer(
        string='Conflicts',
        default=0,
        help="Number of field conflicts detected during this run.",
    )
    error_count = fields.Integer(
        string='Errors',
        default=0,
        help="Number of organisations that failed to sync.",
    )
    skipped_count = fields.Integer(
        string='Skipped',
        default=0,
        help="Number of fetched organizations skipped based on mapping rules.",
    )
    detail_ids = fields.One2many(
        'nhs.ods.sync.detail',
        'sync_run_id',
        string='Sync Details',
    )
    conflict_ids = fields.One2many(
        'nhs.ods.sync.conflict',
        'sync_run_id',
        string='Conflict Records',
    )
    error_log = fields.Text(
        string='Error Log',
        help="Contains any fatal errors or exceptions raised during execution.",
    )
    api_base_url_used = fields.Char(
        string='API URL Used',
        required=True,
        default='https://directory.spineservices.nhs.uk/ORD/2-0-0',
        help="API endpoint URL used for this sync run.",
    )
    delta_since = fields.Date(
        string='Delta Since',
        help="For incremental runs, the LastChangeDate cutoff used.",
    )
    targeted_ods_code = fields.Char(
        string='ODS Code',
        help="Required when Sync Type is 'Targeted'. Enter a single ODS code e.g. RJ1, RW1, 7A6.",
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
    )
    cancel_requested = fields.Boolean(string='Cancel Requested', default=False, copy=False)

    @api.depends('name', 'run_type', 'state')
    def _compute_display_name(self):
        """Compute display name including sequence reference and state."""
        type_labels = dict(self._fields['run_type'].selection)
        state_labels = dict(self._fields['state'].selection)
        for rec in self:
            t = type_labels.get(rec.run_type, rec.run_type or '')
            s = state_labels.get(rec.state, rec.state or '')
            rec.display_name = f'{rec.name} — {t} — {s}'

    @api.depends('started_at', 'completed_at')
    def _compute_duration(self):
        """Compute sync execution duration in minutes."""
        for rec in self:
            if rec.started_at and rec.completed_at:
                delta = rec.completed_at - rec.started_at
                rec.duration = delta.total_seconds() / 60.0
            else:
                rec.duration = 0.0


    @api.model_create_multi
    def create(self, vals_list):
        """Enforce sequence numbering for newly created sync runs."""
        seq = self.env['ir.sequence'].next_by_code('nhs.ods.sync.run')
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = seq or 'SYNC/NEW'
        return super().create(vals_list)

    def action_run(self):
        """Prepare and start sync execution, spawning a background thread if needed."""
        self.ensure_one()
        if self.state not in ('pending',):
            raise UserError(("Only pending runs can be started."))
        self.write({
            'state': 'running',
            'started_at': fields.Datetime.now(),
        })


        if self.run_type == 'targeted':
            # Targeted is a single API call — fast enough to run synchronously
            self.env.cr.flush()
            self._execute_run()
            return

        # Full / incremental / dry_run can take minutes — run in background
        # so the HTTP request returns immediately without timing out.
        self.env.cr.commit()
        self._start_background_run()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title':('Sync Started'),
                'message': ('%s is running in the background. Refresh the page to see progress.') % self.name,
                'type': 'info',
                'sticky': True,
            },
        }

    def _start_background_run(self):
        """Spawn a background thread to process the ODS sync asynchronously."""
        run_id = self.id

        db_name = self.env.cr.dbname

        def _run():
            """Execute the ODS sync run in a separate database transaction context."""
            try:
                import odoo
                from odoo.modules.registry import Registry
                registry = Registry(db_name)
                with registry.cursor() as cr:
                    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                    run = env['nhs.ods.sync.run'].browse(run_id)
                    run._execute_run()
                    cr.commit()
            except Exception:
                _logger.exception("Background ODS sync run %s crashed", run_id)

        t = threading.Thread(target=_run, daemon=True)
        t.start()

    def _execute_run(self):
        """Run the sync engine. Called directly (targeted) or from a background thread.
        Each org commits its own results so progress is visible in real time."""
        from ..services.ods_sync_engine import OdsSyncEngine
        engine = OdsSyncEngine(self.env, self)
        error_msg = None
        try:
            if self.run_type == 'full':
                engine.run_full()
            elif self.run_type == 'incremental':
                since = self.delta_since or self._get_last_sync_date()
                engine.run_delta(since)
            elif self.run_type == 'targeted':
                ods_code = self.targeted_ods_code or self.env.context.get('targeted_ods_code')
                if not ods_code:
                    raise UserError(("Targeted sync requires an ODS code. Please fill in the ODS Code field."))
                engine.run_single(ods_code.strip().upper())
            elif self.run_type == 'dry_run':
                engine.run_full()
        except Exception as exc:
            _logger.exception("ODS sync run %s failed", self.name)
            error_msg = str(exc)

        if error_msg:
            self.write({
                'state': 'failed',
                'completed_at': fields.Datetime.now(),
                'error_log': (self.error_log or '') + f'\nFATAL: {error_msg}',
            })
        else:
            final_state = 'success' if self.error_count == 0 else 'partial'
            self.write({
                'state': final_state,
                'completed_at': fields.Datetime.now(),
            })

    def action_refresh_status(self):
        """Reload this form to show latest progress from the background thread."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_cancel(self):
        """Request cancellation of the background thread."""
        self.ensure_one()
        self.cancel_requested = True
        if self.state == 'pending':
            self.state = 'cancelled'

    def action_view_details(self):
        """Return window action displaying detailed processed records."""
        self.ensure_one()
        list_view = self.env.ref('odoo_nhs_ods_sync.view_nhs_ods_sync_detail_list', raise_if_not_found=False)
        form_view = self.env.ref('odoo_nhs_ods_sync.view_nhs_ods_sync_detail_form', raise_if_not_found=False)
        return {
            'type': 'ir.actions.act_window',
            'name': ('Sync Details — %s') % self.name,
            'res_model': 'nhs.ods.sync.detail',
            'view_mode': 'list,form',
            'views': [(list_view.id if list_view else False, 'list'),
                      (form_view.id if form_view else False, 'form')],
            'domain': [('sync_run_id', '=', self.id)],
            'context': {'default_sync_run_id': self.id},
        }

    def action_view_conflicts(self):
        """Return window action displaying pending conflicts for this run."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': ('Conflicts'),
            'res_model': 'nhs.ods.sync.conflict',
            'view_mode': 'kanban,list,form',
            'domain': [('sync_run_id', '=', self.id)],
            'context': {'default_sync_run_id': self.id},
        }

    def _get_last_sync_date(self):
        """Determine cutoff date for delta sync based on previous runs."""
        last = self.search([
            ('id', '!=', self.id),
            ('state', 'in', ('success', 'partial')),
        ], order='started_at desc', limit=1)
        if last and last.started_at:
            from datetime import timedelta
            return (last.started_at - timedelta(hours=6)).date()
        return None

    @api.model
    def _run_scheduled_delta(self):
        """Cron entrypoint for incremental scheduled delta sync."""
        run = self.create({
            'run_type': 'incremental',
            'triggered_by': 'cron',
            'user_id': self.env.ref('base.user_root').id,
            'state': 'running',
            'started_at': fields.Datetime.now(),
        })
        run._execute_run()

    @api.model
    def _run_scheduled_full(self):
        """Cron entrypoint for scheduled full ODS sync."""
        run = self.create({
            'run_type': 'full',
            'triggered_by': 'cron',
            'user_id': self.env.ref('base.user_root').id,
            'state': 'running',
            'started_at': fields.Datetime.now(),
        })
        run._execute_run()

