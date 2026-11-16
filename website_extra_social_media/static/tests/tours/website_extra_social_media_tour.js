import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("website_extra_social_media_visibility", {
    steps: () => [
        {
            content: "Check configured social media link (instagram) is visible with correct href",
            trigger: ".extra_social_media a.extra_social_media_instagram:not(.d-none)[href*='instagram.example.com']",
        },
        {
            content: "Check unconfigured social media link (github) remains hidden",
            trigger: ".extra_social_media a.extra_social_media_github.d-none",
        },
        {
            content: "Check home link is always visible",
            trigger: ".extra_social_media a.extra_social_media_home:not(.d-none)",
        },
    ],
});
