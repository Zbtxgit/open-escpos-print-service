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


replace_once(
    "app/src/main/proto/settings.proto",
    "  bool skip_white_lines_at_page_end = 17;\n",
    "  bool skip_white_lines_at_page_end = 17;\n  float feed_after_print = 18;\n  bool grayscale_printing = 19;\n",
)

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
custom_fields_block = bottom_margin_block + '''                LabelledTextField(
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
                LabelledSwitch(
                    label = "Grayscale printing",
                    checked = settings.grayscalePrinting,
                    onCheckedChange = { grayscale ->
                        context.updatePrinterSetting(uuid = uuid) {
                            it.setGrayscalePrinting(grayscale)
                        }
                    },
                )
'''
replace_once("app/src/main/java/com/farminos/print/Ui.kt", bottom_margin_block, custom_fields_block)

defaults_old = '''        .setEnabled(false)
        .setDriver(Driver.ESC_POS)
        .setDpi(203)
        .setWidth(5.0F)
        .setHeight(8.0F)
        .setMarginLeft(0.0F)
        .setMarginTop(0.0F)
        .setMarginRight(0.0F)
        .setMarginBottom(0.0F)
        .setCut(true)
'''
defaults_new = '''        .setEnabled(false)
        .setDriver(Driver.ESC_POS)
        .setDpi(203)
        .setWidth(7.2F)
        .setHeight(8.0F)
        .setMarginLeft(0.2F)
        .setMarginTop(0.3F)
        .setMarginRight(0.2F)
        .setMarginBottom(0.3F)
        .setFeedAfterPrint(3.0F)
        .setGrayscalePrinting(false)
        .setCut(true)
'''
replace_once("app/src/main/java/com/farminos/print/Ui.kt", defaults_old, defaults_new)

replace_once(
    "app/src/main/java/com/farminos/print/Drivers.kt",
    "                commands.printImage(EscPosPrinterCommands.bitmapToBytes(it, true))\n",
    "                commands.printImage(EscPosPrinterCommands.bitmapToBytes(it, settings.grayscalePrinting))\n",
)

driver_anchor = '''            delayForLength(pixelsToCm(heightPx, settings.dpi))
        }
        if (settings.cut) {
'''
driver_replacement = '''            delayForLength(pixelsToCm(heightPx, settings.dpi))
        }
        if (settings.feedAfterPrint > 0.0F) {
            var remainingFeedDots = Math.round((settings.feedAfterPrint / 2.54F) * settings.dpi)
            while (remainingFeedDots > 0) {
                val feedChunk = Math.min(remainingFeedDots, 255)
                disconnectOnError {
                    commands.feedPaper(feedChunk)
                }
                remainingFeedDots -= feedChunk
            }
            delayForLength(settings.feedAfterPrint)
        }
        if (settings.cut) {
'''
replace_once("app/src/main/java/com/farminos/print/Drivers.kt", driver_anchor, driver_replacement)

replace_once(
    "app/build.gradle.kts",
    '        applicationId = "com.farminos.print"\n',
    '        applicationId = "com.zbtxgit.escposfeed2"\n',
)
replace_once(
    "app/build.gradle.kts",
    '        versionName = "1.3.1"\n',
    '        versionName = "1.3.1-feed2"\n',
)
replace_once("app/build.gradle.kts", "    compileSdk = 37\n", "    compileSdk = 36\n")
replace_once(
    "app/build.gradle.kts",
    '    buildToolsVersion = "37.0.0"\n    compileSdkMinor = 1\n',
    '    buildToolsVersion = "36.0.0"\n',
)
replace_once("gradle/libs.versions.toml", 'coreKtx = "1.19.0"\n', 'coreKtx = "1.17.0"\n')
replace_once(
    "app/src/main/res/values/strings.xml",
    '<string name="app_name">Open ESC/POS Print Service</string>',
    '<string name="app_name">Open ESC/POS Print Service - Feed v2</string>',
)

print("Feed v2 patch applied successfully.")
