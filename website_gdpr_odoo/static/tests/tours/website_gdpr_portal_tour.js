import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("website_gdpr_portal_tour", {
    steps: () => [
        {
            content: "Request a copy of the contact details",
            trigger: ".o_gdpr_template:contains(Contact Details) .o_gdpr_download",
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "The request is sent",
            trigger: ".o_gdpr_submit .alert-success",
        },
        {
            content: "Go back to the personal data",
            trigger: ".o_gdpr_submit a[href='/my/data_management']",
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "Ask to delete the contact details",
            trigger: ".o_gdpr_template:contains(Contact Details) .o_gdpr_delete",
            run: "click",
        },
        {
            content: "Confirm the deletion request",
            trigger: ".modal.show .o_gdpr_confirm_delete",
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "The delete request is sent",
            trigger: ".o_gdpr_submit .alert-success",
        },
        {
            trigger: ".o_gdpr_submit a[href='/my/data_management']",
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "Open the requests",
            trigger: ".o_gdpr_requests_tab",
            run: "click",
        },
        {
            content: "Both requests are pending",
            trigger: ".o_gdpr_request_table tbody tr:contains(Download Data) .o_gdpr_state_pending",
        },
        {
            trigger: ".o_gdpr_request_table tbody tr:contains(Delete Data) .o_gdpr_state_pending",
        },
    ],
});
