# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhijith PG (odoo@cybrosys.com)
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
#
#############################################################################
import pickle
from ast import literal_eval
from datetime import timedelta
import odoo
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.tools._vendor import sessions


class UserSessionLogin(models.Model):
    """
    Model to store user session login information. Contains information like
    user_id, login_date, logout_date, session duration, device details,
    IP address, etc.
    """
    _name = "user.session.login"
    _description = "User Session Login"

    status = fields.Selection(selection=[('normal', ''),
                                         ('done', ''),
                                         ('blocked', '')], string='Status',
                              help="Status of the user session")
    name = fields.Char(string='Name', help="Sequence number of the session.")
    user_id = fields.Many2one('res.users', string="User", help="Session user")
    sid = fields.Char(string='Session ID', help="Session id")
    login_date = fields.Datetime(string='Login Date', help="Session login date")
    logout_date = fields.Datetime(string='Logout Date',
                                  help="Session logout date")
    session_duration = fields.Char(string='Session Duration',
                                   help="Duration of the session",
                                   compute='_compute_session_duration')
    device = fields.Char(string='Device',
                         help="Device from which the session is created")
    os = fields.Char(string='OS',
                     help="Operating System from which the session is created")
    browser = fields.Char(string='Browser',
                          help="Browser on which the session is logged in")
    ip_address = fields.Char(string='IP', help="IP address of the device")
    state = fields.Selection(selection=[('active', 'Active'),
                                        ('closed', 'Closed')],
                             string='Status', help="State of the session.")
    activity_ids = fields.One2many('user.session.activity', 'login_id',
                                   string='Activities',
                                   readonly=True,
                                   help="All the activities in the selected "
                                        "models in the session")

    @api.model
    def create(self, vals_list):
        """Updating the session sequence when creating a new session record"""
        if not vals_list.get('name'):
            vals_list['name'] = self.env['ir.sequence'].next_by_code(
                'user.session.login.name') or ""
        res = super().create(vals_list)
        if request and request.session:
            request.session.usm_session_id = res.id
        return res

    @api.depends('login_date', 'logout_date')
    def _compute_session_duration(self):
        """Compute session duration"""
        self.session_duration = 0
        for rec in self:
            if rec.login_date and rec.logout_date:
                rec.session_duration = str(rec.logout_date - rec.login_date)
            else:
                rec.session_duration = 0

    def unlink(self):
        """
        Raises a `ValidationError` if any of the User Session Login records
        being deleted have an active session. Only logged-out session user
        session records can be deleted.
        """
        for rec in self:
            if not rec.logout_date:
                raise ValidationError(
                    "%s is active. Only logged out session records can be "
                    "deleted" % rec.name)
        return super().unlink()

    def action_button_force_logout(self):
        """Logs out the user by clearing the session data."""
        self.ensure_one()
        self.update({'state': 'closed',
                     'status': 'blocked'})
        state_mapped = self.env['user.session.login'].sudo().search(
            [('user_id', '=', self.user_id.id)]).mapped('state')
        if 'active' not in state_mapped:
            self.sudo().user_id.status = 'blocked'
        try:
            self.update({'logout_date': fields.Datetime.now()})
            path = odoo.tools.config.session_dir
            store = sessions.FilesystemSessionStore(
                path, session_class=odoo.http.OpenERPSession,
                renew_missing=True)
            session_fname = store.get_session_filename(self.sid)
            sess_file = open(session_fname, 'rb')
            sess = pickle.load(sess_file)
            # updating the sess file
            sess['login'] = None
            sess['uid'] = None
            sess['session_token'] = None
            sess['context'] = {}
            sess_file = open(session_fname, 'wb')
            pickle.dump(sess, sess_file)
        except FileNotFoundError:
            self.update({'logout_date': fields.Datetime.now()})

    def clear_records(self):
        """
        Clears all the user session records that have a logout_date older
        than the number of days specified in the settings.
        """
        records = self.search([])
        for rec in records:
            if rec.logout_date and fields.Datetime.now() > rec.logout_date + \
                    timedelta(days=literal_eval(
                        self.env['ir.config_parameter'].sudo().get_param(
                            'user_session_management.records_retain_period')))\
                    and self.env['ir.config_parameter'].sudo().get_param(
                            'user_session_management.clear_log'):
                rec.activity_ids.unlink()
                rec.unlink()
