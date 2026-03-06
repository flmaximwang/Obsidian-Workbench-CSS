module.exports = () => {
    const settings = [];

    return {
        postcssPlugin: "collect-settings",

        Comment(setting) {
            if (setting.text.includes("@settings")) {
                settings.push(setting.text.replace("@settings", ""));
                setting.remove();
            }
        },

        OnceExit(root) {
            if (settings.length > 0) {
                root.prepend({
                    type: "comment",
                    text: "@settings" + settings.join("") + "\n"
                });
            }
        }
    };
}

module.exports.postcss = true;