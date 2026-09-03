from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if new in text:
        print(f"{path}: already patched")
        return
    if old not in text:
        raise RuntimeError(f"Could not find expected text in {path}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{path}: patched")


# 1) Persist the new per-printer setting. Field 18 is new and keeps protobuf compatibility.
replace_once(
    "app/src/main/proto/settings.proto",
    "  bool skip_white_lines_at_page_end = 17;\n",
    "  bool skip_white_lines_at_page_end = 17;\n  float feed_after_print = 18;\n",
)

# 2) Add the setting to the UI immediately after the margin settings.
bottom_margin_block = '''                LabelledTextField(
                    label = "Bottom margin (cm)",
                    value = settings.marginBottom.toString(),
                    transform = { cm ->
                        cm.toFloatOrNull()
                    },
                    onValueChange = { cm ->
                        context.updatePrinterSetting(uuid = uuid) {
                            it.setMarginBottom(cm)
                        }
                    },
                )
'''
feed_field_block = bottom_margin_block + '''                LabelledTextField(
                    label = "Feed after print (cm)",
                    value = settings.feedAfterPrint.toString(),
                    transform = { cm ->
                        cm.toFloatOrNull()?.takeIf { it >= 0.0F }
                    },
                    onValueChange = { cm ->
                        context.updatePrinterSetting(uuid = uuid) {
                            it.setFeedAfterPrint(cm)
                        }
                    },
                )
'''
replace_once(
    "app/src/main/java/com/farminos/print/Ui.kt",
    bottom_margin_block,
    feed_field_block,
)

# New printers default to 2 cm. Existing protobuf data safely defaults to 0 until edited.
replace_once(
    "app/src/main/java/com/farminos/print/Ui.kt",
    "        .setMarginBottom(0.0F)\n        .setCut(true)\n",
    "        .setMarginBottom(0.0F)\n        .setFeedAfterPrint(2.0F)\n        .setCut(true)\n",
)

# 3) Feed the requested physical distance after the bitmap and before cut/reset.
# DantSu feedPaper() accepts printer dots, so convert cm using the configured DPI.
driver_anchor = '''            delayForLength(pixelsToCm(heightPx, settings.dpi))
        }
        if (settings.cut) {
'''
driver_replacement = '''            delayForLength(pixelsToCm(heightPx, settings.dpi))
        }
        if (settings.feedAfterPrint > 0.0F) {
            val feedDots = Math.round((settings.feedAfterPrint / 2.54F) * settings.dpi)
            if (feedDots > 0) {
                disconnectOnError {
                    commands.feedPaper(feedDots)
                }
                // Let the printer physically advance before a cut or reset command follows.
                delayForLength(settings.feedAfterPrint)
            }
        }
        if (settings.cut) {
'''
replace_once(
    "app/src/main/java/com/farminos/print/Drivers.kt",
    driver_anchor,
    driver_replacement,
)

# 4) Give this test build its own Android package so it can coexist with the Play Store app.
replace_once(
    "app/build.gradle.kts",
    '        applicationId = "com.farminos.print"\n',
    '        applicationId = "com.zbtxgit.escposfeed"\n',
)
replace_once(
    "app/build.gradle.kts",
    '        versionName = "1.3.1"\n',
    '        versionName = "1.3.1-feed1"\n',
)

# Make the custom build easy to distinguish in Android settings / print-service selection.
replace_once(
    "app/src/main/res/values/strings.xml",
    '<string name="app_name">Open ESC/POS Print Service</string>',
    '<string name="app_name">Open ESC/POS Print Service - Feed</string>',
)

print("Feed-after-print patch applied successfully.")
