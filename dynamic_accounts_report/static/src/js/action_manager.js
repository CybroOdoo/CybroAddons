



//
//import { registry } from "@web/core/registry";
//import { download } from "@web/core/network/download";
//import framework from 'web.framework';
//import session from 'web.session';
//async function dynamicXlsxDownload({ env, action }) {
//
//    framework.blockUI();
//        var def = $.Deferred();
//        download._download({
//            url: '/dynamic_xlsx_reports',
//            data: action.data,
//            success: def.resolve.bind(def),
//            error: (error) => this.call('crash_manager', 'rpc_error', error),
////            complete: framework.unblockUI,
//        });
//        framework.unblockUI();
//        return def;
//
//}
//
//registry.category("action_handlers")
//    .add('ir_actions_dynamic_xlsx_download', dynamicXlsxDownload);


//odoo.define('dynamic_accounts_report.action_manager', function (require) {
//    'use strict';
//
//    downloadXlsx: function (action){
//            framework.blockUI();
//                download._download({
//                    url: '/dynamic_xlsx_reports',
//                    data: action.data,
//                    complete: framework.unblockUI,
//                    error: (error) => this.call('crash_manager', 'rpc_error', error),
//                });
//            framework.unblockUI();
//            },
//
//
//            });


//odoo.define('dynamic_accounts_report.action_manager', function (require) {
//    'use strict';
//
//    downloadXlsx: function (action){
//            framework.blockUI();
//                session.get_file({
//                    url: '/dynamic_xlsx_reports',
//                    data: action.data,
//                    complete: framework.unblockUI,
//                    error: (error) => this.call('crash_manager', 'rpc_error', error),
//                });
////            framework.unblockUI();
//            },
//
//
//            });