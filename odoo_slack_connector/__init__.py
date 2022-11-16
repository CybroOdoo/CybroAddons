from . import models


def slack_uninstall_hook(cr, registry):
    cr.execute("DELETE FROM res_partner WHERE is_slack_user='true'")
    cr.execute("DELETE FROM mail_channel WHERE is_slack='true'")
    cr.execute("DELETE FROM res_users WHERE is_slack_internal_users='true'")
    cr.commit()
