# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
###############################################################################
import contextlib
import glob
import os

from odoo.http import root


@contextlib.contextmanager
def writable_cursor(env):
    """Yield a cursor that can write.

    Odoo serves many routes on a read only cursor. Like the core does for
    the device log, a read/write cursor is opened in this case.
    """
    if env.cr.readonly:
        env.cr.rollback()
        with env.registry.cursor(readonly=False) as cursor:
            yield cursor
    else:
        yield env.cr


def clear_session_history(sid):
    """Delete the session file of the given session id.

    :return: True when the session no longer exists on the disk, False when
        it could not be removed.
    """
    if not sid:
        return True
    try:
        session_path = root.session_store.get_session_filename(sid)
    except ValueError:  # not a valid session id, so there is no file
        return True
    try:
        os.remove(session_path)
    except FileNotFoundError:  # already gone
        return True
    except OSError:
        return False
    return True


def clear_all_session_files():
    """Delete every session file of the session store.

    :return: the number of deleted files.
    """
    deleted = 0
    for path in glob.iglob(os.path.join(root.session_store.path, '*', '*')):
        with contextlib.suppress(OSError):
            os.unlink(path)
            deleted += 1
    return deleted
