import {
    clickOnSave,
    clickOnSnippet,
    insertSnippet,
    registerWebsitePreviewTour,
} from "@website/js/tours/tour_utils";

const LINK_INPUT = "[data-action-id='dynamicLink'] input";
const YOUTUBE_EMBED = "https://www.youtube.com/embed/dQw4w9WgXcQ";

function setLink(content, link) {
    return [
        {
            content,
            trigger: LINK_INPUT,
            run: `edit ${link}`,
        },
        {
            content: "Validate the link",
            trigger: LINK_INPUT,
            run: "press Enter",
        },
    ];
}

registerWebsitePreviewTour(
    "dynamic_link_snippet_tour",
    {
        url: "/",
        edition: true,
    },
    () => [
        ...insertSnippet({ id: "s_dynamic_link", name: "Dynamic Link" }),
        ...clickOnSnippet({ id: "s_dynamic_link" }),
        ...setLink("Paste a YouTube watch link", "https://youtu.be/dQw4w9WgXcQ"),
        {
            content: "The watch link is converted to an embed link inside an iframe",
            trigger: `:iframe .s_dynamic_link[data-link-url='${YOUTUBE_EMBED}'] iframe[src='${YOUTUBE_EMBED}']`,
        },
        ...setLink("Paste an unsafe link", "javascript:alert(1)"),
        {
            content: "The unsafe link is refused and the iframe is removed",
            trigger: ":iframe .s_dynamic_link:not([data-link-url]):not(:has(iframe))",
        },
        ...setLink("Paste a normal page link", "https://www.example.com/"),
        {
            content: "The page link is shown inside an iframe",
            trigger: ":iframe .s_dynamic_link[data-link-url='https://www.example.com/'] iframe[src='https://www.example.com/']",
        },
        ...clickOnSave(),
        {
            content: "The saved page still shows the iframe",
            trigger: ":iframe .s_dynamic_link[data-link-url='https://www.example.com/'] iframe[src='https://www.example.com/']",
        },
    ]
);
