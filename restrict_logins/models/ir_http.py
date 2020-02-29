# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Milind Mohan(<https://www.cybrosys.com>)
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
from datetime import datetime, timedelta

import werkzeug
import werkzeug.exceptions
import werkzeug.routing
import werkzeug.urls
import werkzeug.utils

from odoo import models, http, SUPERUSER_ID
from odoo.exceptions import AccessDenied
from odoo.http import request

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _authenticate(cls, auth_method='user'):
        try:
            if request.session.uid:
                try:
                    uid = request.session.uid
                    user_pool = request.env['res.users'].with_user(SUPERUSER_ID).browse(uid)
                    sid = request.session.sid
                    last_update = user_pool.last_update
                    if last_update:
                        update_diff = (datetime.now() - last_update).total_seconds() / 60.0
                        # update sid and date if last update is above 1 min
                        if uid and (update_diff > 1 or sid != user_pool.sid):
                            now = datetime.now()
                            exp_date = datetime.now() + timedelta(minutes=45)
                            query = """update res_users set sid = '%s',
                            last_update = '%s',exp_date = '%s' where id = %s
                            """ % (sid, now, exp_date, uid)
                            request.env.cr.execute(query)
                    request.session.check_security()
                    # what if error in security.check()
                    #   -> res_users.check()
                    #   -> res_users._check_credentials()
                except (AccessDenied, http.SessionExpiredException):
                    # All other exceptions mean undetermined status (e.g. connection pool full),
                    # let them bubble up
                    request.session.logout(keep_db=True)
            if request.uid is None:
                getattr(cls, "_auth_method_%s" % auth_method)()
        except (AccessDenied, http.SessionExpiredException,
                werkzeug.exceptions.HTTPException):
            raise
        except Exception:
            _logger.info("Exception during request Authentication.",
                         exc_info=True)
            raise AccessDenied()
        return auth_method
