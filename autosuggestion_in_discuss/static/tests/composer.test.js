import { after, describe, expect, test } from "@odoo/hoot";
import { mockFetch } from "@odoo/hoot-mock";
import { Composer } from "@mail/core/common/composer";
import "@autosuggestion_in_discuss/js/composer";

describe("autosuggestion_in_discuss composer", () => {
    function setupTextareas(userValue = "") {
        const userInput = document.createElement("textarea");
        userInput.id = "userInputText";
        userInput.value = userValue;
        const suggestion = document.createElement("textarea");
        suggestion.id = "autoCompleteText";
        document.body.append(userInput, suggestion);
        after(() => {
            userInput.remove();
            suggestion.remove();
        });
        return { userInput, suggestion };
    }

    function mockSuggestions(suggestions) {
        mockFetch(() => ({ result: suggestions }));
    }

    test("shows the first alphabetically sorted, case-insensitive prefix match", async () => {
        const { userInput, suggestion } = setupTextareas("he");
        mockSuggestions(["Hello there", "help", "Good morning"]);

        Composer.prototype.onKeyupTextarea.call({}, {});
        await new Promise((resolve) => setTimeout(resolve));

        expect(suggestion.value).toBe("Hello there");
        expect(userInput.value).toBe("he");
    });

    test("clears the suggestion when the input is empty or whitespace", () => {
        const { suggestion } = setupTextareas("   ");
        suggestion.value = "old suggestion";

        Composer.prototype.onKeyupTextarea.call({}, {});

        expect(suggestion.value).toBe("");
    });

    test("clears the suggestion when there is no matching prefix", async () => {
        const { suggestion } = setupTextareas("xyz");
        suggestion.value = "old suggestion";
        mockSuggestions(["Hello there"]);

        Composer.prototype.onKeyupTextarea.call({}, {});
        await new Promise((resolve) => setTimeout(resolve));

        expect(suggestion.value).toBe("");
    });

    test("escapes regular expression characters in the typed prefix", async () => {
        const { suggestion } = setupTextareas("what?");
        mockSuggestions(["what? next", "whatX next"]);

        Composer.prototype.onKeyupTextarea.call({}, {});
        await new Promise((resolve) => setTimeout(resolve));

        expect(suggestion.value).toBe("what? next");
    });

    test("accepts suggestion on Tab and prevents default", async () => {
        const { userInput, suggestion } = setupTextareas("he");
        mockSuggestions(["Hello there"]);

        const instance = {
            props: { composer: { composerText: "he" } },
        };
        await Composer.prototype.onKeyupTextarea.call(instance, {});
        expect(suggestion.value).toBe("Hello there");

        let defaultPrevented = false;
        const ev = {
            key: "Tab",
            preventDefault() {
                defaultPrevented = true;
            },
        };
        Composer.prototype.onKeydown.call(instance, ev);

        expect(defaultPrevented).toBe(true);
        expect(userInput.value).toBe("Hello there");
        expect(instance.props.composer.composerText).toBe("Hello there");
        expect(suggestion.value).toBe("");
    });

    test("does not prevent default or set space on Tab when there is no matching suggestion", async () => {
        const { userInput, suggestion } = setupTextareas("xyz");
        mockSuggestions(["Hello there"]);

        const instance = {
            props: { composer: { composerText: "xyz" } },
        };
        await Composer.prototype.onKeyupTextarea.call(instance, {});
        expect(suggestion.value).toBe("");

        let defaultPrevented = false;
        const ev = {
            key: "Tab",
            preventDefault() {
                defaultPrevented = true;
            },
        };
        Composer.prototype.onKeydown.call(instance, ev);

        expect(defaultPrevented).toBe(false);
        expect(userInput.value).toBe("xyz");
        expect(suggestion.value).toBe("");
    });

    test("accepts suggestion on ArrowRight when cursor is at the end", async () => {
        const { userInput, suggestion } = setupTextareas("he");
        userInput.selectionStart = 2;
        mockSuggestions(["Hello there"]);

        const instance = {
            props: { composer: { composerText: "he" } },
        };
        await Composer.prototype.onKeyupTextarea.call(instance, {});
        expect(suggestion.value).toBe("Hello there");

        let defaultPrevented = false;
        const ev = {
            key: "ArrowRight",
            preventDefault() {
                defaultPrevented = true;
            },
        };
        Composer.prototype.onKeydown.call(instance, ev);

        expect(defaultPrevented).toBe(true);
        expect(userInput.value).toBe("Hello there");
        expect(suggestion.value).toBe("");
    });

    test("clears suggestion on Enter keydown", async () => {
        const { suggestion } = setupTextareas("he");
        mockSuggestions(["Hello there"]);

        const instance = {
            props: { composer: { composerText: "he" } },
        };
        await Composer.prototype.onKeyupTextarea.call(instance, {});
        expect(suggestion.value).toBe("Hello there");

        const ev = {
            key: "Enter",
            preventDefault() {},
        };
        Composer.prototype.onKeydown.call(instance, ev);

        expect(suggestion.value).toBe("");
    });

    test("supports instance refs to avoid picking wrong composer elements across windows", () => {
        const user1 = document.createElement("textarea");
        const suggest1 = document.createElement("textarea");
        const user2 = document.createElement("textarea");
        const suggest2 = document.createElement("textarea");

        const instance1 = {
            ref: () => user1,
            autoCompleteRef: () => suggest1,
        };
        const instance2 = {
            ref: () => user2,
            autoCompleteRef: () => suggest2,
        };

        expect(Composer.prototype._getUserTextarea.call(instance1)).toBe(user1);
        expect(Composer.prototype._getAutoCompleteTextarea.call(instance1)).toBe(suggest1);
        expect(Composer.prototype._getUserTextarea.call(instance2)).toBe(user2);
        expect(Composer.prototype._getAutoCompleteTextarea.call(instance2)).toBe(suggest2);
    });
});
