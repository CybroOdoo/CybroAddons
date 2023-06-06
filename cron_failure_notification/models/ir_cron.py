# -*- coding: utf-8 -*-
# ##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: MOHAMMED DILSHAD TK (odoo@cybrosys.com)
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
################################################################################
import datetime
import logging
import odoo
import time
from odoo import api, models
from odoo.fields import Datetime, _logger


class IrCron(models.Model):
    """ Inherits ir cron for add a feature that sends mail to admin
     each day, if any cron failed """
    _name = 'ir.cron'
    _inherit = ['ir.cron', 'mail.thread']

    @api.model
    def _callback(self, cron_name, server_action_id, job_id):
        """ Run the method associated to a given job. It takes care of logging
        and exception handling. Note that the user running the server action
        is the user calling this method. """
        try:
            if self.pool != self.pool.check_signaling():
                # the registry has changed, reload self in the new registry
                self.env.reset()
            log_depth = (None if _logger.isEnabledFor(logging.DEBUG) else 1)
            odoo.netsvc.log(_logger, logging.DEBUG, 'cron.object.execute',
                            (self._cr.dbname, self._uid, '*', cron_name,
                             server_action_id), depth=log_depth)
            start_time = False
            _logger.info('Starting job `%s`.', cron_name)
            if _logger.isEnabledFor(logging.DEBUG):
                start_time = time.time()
            self.env['ir.actions.server'].browse(server_action_id).run()
            _logger.info('Job `%s` done.', cron_name)
            if start_time and _logger.isEnabledFor(logging.DEBUG):
                end_time = time.time()
                _logger.debug('%.3fs (cron %s, server action %d with uid %d)',
                              end_time - start_time, cron_name,
                              server_action_id, self.env.uid)
            self.pool.signal_changes()
        except Exception as exception:
            self.pool.reset_changes()
            _logger.exception(
                "Call from cron %s for server action #%s failed in Job #%s",
                cron_name, server_action_id, job_id)
            if exception:
                self.env['failure.history'].create({
                    'name': cron_name,
                    'error': str(exception),
                })

    def mail_send_cron(self):
        """ If any cron's failed a notification email will send to admin """
        start_of_day = Datetime.today()
        end_of_day = datetime.datetime.combine(start_of_day, datetime.time.max)
        failure = self.env['failure.history'].search(
            [('create_date', '>', start_of_day),
             ('create_date', '<', end_of_day)])
        if failure:
            admin_mail = self.env['res.groups'].search(
                [('category_id', '=', 'Administration'),
                 ('name', '=', 'Access Rights')]).users.login
            email_values = {'admin_mail': admin_mail}
            mail_template = self.env.ref(
                'cron_failure_notification.mail_template_cron_error')
            mail_template.with_context(email_values).send_mail(self.id,
                                                               force_send=True)
