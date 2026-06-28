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
from contextlib import contextmanager
from types import SimpleNamespace
import odoo.http as http


@contextmanager
def wkhtmltopdf_request(env):
    """
    Provide a minimal `odoo.http.request` for PDF generation executed outside a
    real HTTP request (e.g. background threads).

    Odoo only passes a cookie jar to wkhtmltopdf when `odoo.http.request` exists.
    Without that cookie jar, wkhtmltopdf can't load `/web/assets` in multi-db
    mode unless `dbfilter` forces a single database, resulting in missing CSS.
    """
    allowed_company_ids = env.context.get("allowed_company_ids")
    if isinstance(allowed_company_ids, (list, tuple)):
        allowed_company_ids = list(allowed_company_ids)
    else:
        allowed_company_ids = env.user.company_ids.ids

    session_context = {}
    lang = env.context.get("lang") or env.user.lang
    tz = env.context.get("tz") or env.user.tz
    if lang:
        session_context["lang"] = lang
    if tz:
        session_context["tz"] = tz
    if allowed_company_ids:
        session_context["allowed_company_ids"] = allowed_company_ids

    session_dict = {
        "db": env.cr.dbname,
        "uid": env.uid,
        "login": env.user.login if env.uid else None,
        # This must be JSON-serializable: Odoo sessions are persisted as JSON.
        "context": session_context,
    }
    
    class MockSession(dict):
        def __getattr__(self, item):
            return self.get(item)
            
    session = MockSession(session_dict)
            
    fake_request = SimpleNamespace(session=session, db=session["db"])
    http._request_stack.push(fake_request)
    try:
        yield
    finally:
        http._request_stack.pop()
