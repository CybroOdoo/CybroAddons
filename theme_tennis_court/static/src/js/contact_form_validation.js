/** @odoo-module **/

document.addEventListener("click", function (ev) {
    const button = ev.target.closest(".s_website_form_send");
    if (!button) return;

    // Handle contact form
    const contactForm = button.closest("form#tc_contactus_form");
    if (contactForm) {
        contactForm.classList.add("was-validated");
        let hasError = false;
        contactForm.querySelectorAll("[required]").forEach(function (field) {
            if (!field.value.trim()) {
                field.classList.add("tc-field-error");
                hasError = true;
            } else {
                field.classList.remove("tc-field-error");
            }
        });
        if (hasError) {
            ev.preventDefault();
            ev.stopPropagation();
        }
        return;
    }

    // Handle membership application form
    const joinWrapper = button.closest(".join-form-wrapper");
    if (joinWrapper) {
        const joinForm = joinWrapper.querySelector("form");
        if (!joinForm) return;

        let hasError = false;
        joinForm.querySelectorAll(".form-control, select")
            .forEach(function (field) {
            const isRequired = field.hasAttribute("required");
            if (isRequired && !field.value.trim()) {
                field.classList.add("tc-field-error");
                hasError = true;
            } else {
                field.classList.remove("tc-field-error");
            }
        });

        if (hasError) {
            ev.preventDefault();
            ev.stopPropagation();
        }
    }
});
