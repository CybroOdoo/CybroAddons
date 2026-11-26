# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
"""Company scope shared by the accounting reports of this module."""
from odoo import models


def get_report_company(env, form=None):
    """Return the company a report is printed for.

    Looks at the wizard's ``company_id`` (an id, an ``(id, name)`` pair as
    returned by ``read()``/JSON, or a record), then at ``used_context``, then
    at the environment context. Falls back to the current company.
    """
    form = form or {}
    company = form.get('company_id') \
        or (form.get('used_context') or {}).get('company_id') \
        or env.context.get('company_id')
    if isinstance(company, models.BaseModel):
        company = company[:1].id
    elif isinstance(company, (list, tuple)):
        company = company[0] if company else False
    return env['res.company'].browse(company or []).exists() \
        or env.company


def get_report_branches(company):
    """The report company and its branches selected in the company switcher
    (see ``res.company._accessible_branches``). Falls back to the company
    alone when it is not selected itself (e.g. called from a cron)."""
    return company._accessible_branches() or company


def get_report_journal_domain(company, domain=None):
    """Domain of the journals a report of ``company`` can use: those usable
    by the company or one of its selected branches. As in core
    (``account.journal._check_company_domain``), a branch also posts in the
    journals of its parent companies."""
    Journal = company.env['account.journal']
    return list(domain or []) + Journal._check_company_domain(
        get_report_branches(company))
