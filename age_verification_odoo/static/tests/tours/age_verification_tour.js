import { registry } from "@web/core/registry";

const LOCKED_LOGIN = ".oe_signup_form[inert] input[name='login']:disabled";

function setBirthDate(value) {
    document.querySelector(".o_age_verify_date").value = value;
}

registry.category("web_tour.tours").add("age_verification_tour", {
    steps: () => {
        const today = new Date();
        const childYear = today.getFullYear() - 10;
        const childDate = `${childYear}-01-01`;
        return [
            {
                content: "The signup form is locked behind the popup",
                trigger: `${LOCKED_LOGIN}:not(:visible), ${LOCKED_LOGIN}`,
            },
            {
                content: "Submit without a date",
                trigger: ".o_age_verify_submit",
                run: "click",
            },
            {
                content: "A date is required",
                trigger: ".o_age_verify_invalid:not(.d-none)",
            },
            {
                content: "Enter the date of birth of a child",
                trigger: ".o_age_verify_date",
                run: () => setBirthDate(childDate),
            },
            {
                content: "Submit the date of a child",
                trigger: ".o_age_verify_submit",
                run: "click",
            },
            {
                content: "The child is refused",
                trigger: ".o_age_verify_denied:not(.d-none)",
            },
            {
                content: "The form stays locked for the child",
                trigger: `${LOCKED_LOGIN}:not(:visible), ${LOCKED_LOGIN}`,
            },
            {
                content: "Enter the date of birth of an adult",
                trigger: ".o_age_verify_date",
                run: () => setBirthDate("1990-01-01"),
            },
            {
                content: "Submit the date of an adult",
                trigger: ".o_age_verify_submit",
                run: "click",
            },
            {
                content: "The popup is closed",
                trigger: ".o_age_verify.d-none:not(:visible)",
            },
            {
                content: "The signup form is unlocked",
                trigger: ".oe_signup_form:not([inert]) input[name='login']:enabled",
            },
        ];
    },
});

registry.category("web_tour.tours").add("age_verification_invite_tour", {
    steps: () => [
        {
            content: "The visitor has not confirmed an age in this session",
            trigger: ".o_age_verify:not(:visible)",
            run: () => {
                if (sessionStorage.getItem("age_verification_odoo.verified")) {
                    throw new Error("The age was already confirmed in this session");
                }
            },
        },
        {
            content: "The invitation link skips the popup",
            trigger: ".o_age_verify.d-none:not(:visible)",
        },
        {
            content: "The signup form of the invited user is unlocked",
            trigger: ".oe_signup_form:not([inert]) input[name='login']",
        },
    ],
});
