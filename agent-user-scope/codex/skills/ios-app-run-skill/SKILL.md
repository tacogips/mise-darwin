---
name: ios-app-run-skill
description: Build, install, launch, and verify the Your Body iOS/iPadOS app from the checked-in Xcode project. Use when Codex is asked to run, open, start, install, debug-launch, screenshot, or diagnose the local Your Body iOS app in Simulator or on a connected device, especially when Xcode schemes, iOS SDK/runtime support, assets, AppIntents metadata, Info.plist resources, StoreKit files, or HealthKit entitlements may affect launch.
---

# Your Body iOS App Run

## Goal

Get the checked-in `YourBody` app visibly running on iOS Simulator or a connected iOS/iPadOS device, then prove it with the build result, installed bundle identifier, launch PID, and screenshot path. If it cannot run, report the exact blocker and classify it as project code, Xcode platform support, signing, packaging, or runtime environment.

This skill is the reusable runbook for the installable iOS app surface created in this repository:

- Project: `YourBody.xcodeproj`
- Shared scheme: `YourBody`
- Bundle identifier: `com.tacogips.yourbody`
- Preferred local target: iOS Simulator first, physical device only when connected and signing is configured

## Required Context

Read the repository instructions first:

```bash
sed -n '1,220p' AGENTS.md
```

Respect these project constraints while running the app:

- Do not commit API keys, HealthKit data, transcripts, food photos, journals, DerivedData, screenshots, or temporary app bundles.
- Keep provider calls, encrypted journal behavior, StoreKit entitlement behavior, HealthKit semantics, and App Intent behavior unchanged while diagnosing launch.
- Use `scripts/verify.sh` for standard verification before handoff when code or project files changed.
- Use `scripts/verify.sh --xcode-macos` when app-facing or Xcode-facing files changed.
- Use `scripts/verify.sh --xcode-ios` when iOS packaging, app resources, entitlements, Info.plist, AppIntents, or Xcode project settings changed.

## Inspect State

Run these before building:

```bash
git status --short --branch
xcodebuild -version
xcodebuild -showsdks
xcrun simctl list runtimes
xcrun simctl list devices available
rg --files -g '*.xcodeproj' -g '*.xcworkspace' -g '*.xcscheme' -g 'Package.swift'
xcodebuild -list -project YourBody.xcodeproj
xcodebuild -project YourBody.xcodeproj -scheme YourBody -showdestinations
```

Prefer the checked-in Xcode app surface:

- Project: `YourBody.xcodeproj`
- Scheme: `YourBody`
- Bundle identifier: `com.tacogips.yourbody`
- Device families: iPhone and iPad
- App resources: `YourBody/Resources/Info.plist`, `YourBody/Resources/PrivacyInfo.xcprivacy`, `YourBody/Resources/YourBody.storekit`, `YourBody/Resources/Assets.xcassets`
- Entitlements: `YourBody/YourBody.entitlements`

The SwiftPM `YourBodyApp` scheme is useful for package, macOS, and Catalyst checks, but it is not the preferred surface for an installable iOS `.app` when `YourBody.xcodeproj` is present.

## Installed App Fast Path

When the user says the app was just installed, verify and launch the installed app before rebuilding:

```bash
scripts/verify-ios-installed-launch.sh
```

Use the checked-in verifier when present because it reports the installed app container, bundle id, executable, launch PID, and screenshot path consistently. It proves launch of the already-installed app only; it does not prove the installed app was built from the current source.

```bash
BUNDLE_ID="com.tacogips.yourbody"
xcrun simctl list devices booted
xcrun simctl get_app_container booted "$BUNDLE_ID" app
open -a Simulator
xcrun simctl launch booted "$BUNDLE_ID"
xcrun simctl io booted screenshot /tmp/your-body-ios-launch.png
```

If `get_app_container` fails, the app is not installed on the currently booted simulator. Continue with the Simulator Launch Workflow and reinstall the freshly built app.

For a stronger installed-app launch proof, use the exact evidence-oriented sequence:

```bash
BUNDLE_ID="com.tacogips.yourbody"
xcrun simctl list devices booted
APP_CONTAINER="$(xcrun simctl get_app_container booted "$BUNDLE_ID" app)"
printf '%s\n' "$APP_CONTAINER"
/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$APP_CONTAINER/Info.plist"
/usr/libexec/PlistBuddy -c 'Print :CFBundleExecutable' "$APP_CONTAINER/Info.plist"
open -a Simulator
xcrun simctl launch booted "$BUNDLE_ID"
xcrun simctl io booted screenshot /tmp/your-body-ios-launch.png
file /tmp/your-body-ios-launch.png
ls -lh /tmp/your-body-ios-launch.png
```

Treat this as launch evidence for the already-installed app on the booted simulator. It proves the installed bundle path, bundle identifier, executable name, launch PID, and screenshot file. It does not prove that the installed app was built from the current source unless the current turn also built and installed it.

Recent known-good local fast-path example:

- Device: `iPhone 17 Pro`
- Runtime: iOS `26.4`
- UDID: `A5684A4D-FB37-4B83-AEA6-F79B4903DE0F`
- Bundle identifier: `com.tacogips.yourbody`
- Executable: `YourBody`
- Launch output shape: `com.tacogips.yourbody: <pid>`
- Screenshot path: `/tmp/your-body-ios-launch.png`
- Expected visible state when onboarding is incomplete: Setup screen with `Your Body` local-first onboarding copy.

If `launch` fails, collect recent logs before rebuilding so launch-time failures are not erased:

```bash
xcrun simctl spawn booted log show --style compact --last 2m \
  --predicate 'process == "SpringBoard" OR eventMessage CONTAINS[c] "com.tacogips.yourbody"'
```

## Simulator Launch Workflow

1. Pick an available bootable iPhone or iPad destination from `xcrun simctl list devices available` or `xcodebuild -showdestinations`.

2. Boot the simulator and open Simulator.app:

   ```bash
   DEVICE_NAME="iPhone 17 Pro"
   xcrun simctl boot "$DEVICE_NAME" || true
   open -a Simulator
   ```

3. Build the app for that destination:

   ```bash
   DERIVED_DATA="/tmp/YourBodyIOSRun"
   rm -rf "$DERIVED_DATA"
   xcodebuild \
     -project YourBody.xcodeproj \
     -scheme YourBody \
     -destination "platform=iOS Simulator,name=${DEVICE_NAME},OS=latest" \
     -derivedDataPath "$DERIVED_DATA" \
     build
   ```

4. Locate and inspect the built app:

   ```bash
   APP_PATH="$(find "$DERIVED_DATA/Build/Products" -path '*-iphonesimulator/YourBody.app' -print -quit)"
   test -n "$APP_PATH"
   /usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$APP_PATH/Info.plist"
   /usr/libexec/PlistBuddy -c 'Print :CFBundleExecutable' "$APP_PATH/Info.plist"
   ```

5. Install, launch, and screenshot:

   ```bash
   BUNDLE_ID="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$APP_PATH/Info.plist")"
   xcrun simctl install booted "$APP_PATH"
   xcrun simctl launch booted "$BUNDLE_ID"
   xcrun simctl io booted screenshot /tmp/your-body-ios-launch.png
   ```

6. Report the exact device/runtime, build command status, installed bundle id, launch PID, and screenshot path.

If multiple simulators are booted, use the device UDID consistently instead of `booted`:

```bash
DEVICE_UDID="$(xcrun simctl list devices booted | sed -n 's/.*(\([0-9A-F-]\{36\}\)).*/\1/p' | head -n 1)"
xcrun simctl install "$DEVICE_UDID" "$APP_PATH"
xcrun simctl launch "$DEVICE_UDID" "$BUNDLE_ID"
xcrun simctl io "$DEVICE_UDID" screenshot /tmp/your-body-ios-launch.png
```

## Connected Device Workflow

Use a physical device only when it is connected, trusted, and signing is configured. Do not disable signing for physical-device verification.

```bash
xcrun xctrace list devices
xcodebuild \
  -project YourBody.xcodeproj \
  -scheme YourBody \
  -destination 'generic/platform=iOS' \
  -derivedDataPath /tmp/YourBodyIOSDevice \
  build
```

If signing fails, report it as a signing blocker and include the failing `xcodebuild` message. Do not work around physical-device signing by editing entitlements or using ad-hoc simulator-only packaging.

## Failure Triage

- If `YourBody.xcodeproj` or the shared `YourBody` scheme is missing, the repo no longer has the checked-in installable app target. Use `rg --files -g '*.xcodeproj' -g '*.xcscheme'` and report the missing project or scheme.
- If `xcodebuild -showdestinations` lists only macOS or Catalyst for the SwiftPM package, do not claim there is an installable iOS app. Switch to `YourBody.xcodeproj` or report that an iOS app target is missing.
- If Xcode reports an iOS SDK/runtime mismatch, missing iOS platform support, or `CoreSimulator is out of date`, classify it as Xcode platform support. Run `scripts/verify.sh --xcode-ios` to capture the repo's fallback behavior.
- If `actool` reports no simulator runtime version available for the `iphonesimulator` SDK, classify full Simulator packaging as blocked until matching Xcode iOS platform support is installed.
- If AppIntents metadata extraction fails, treat it as a real iOS packaging blocker. Do not suppress metadata extraction for final verification.
- If install fails with missing bundle metadata, inspect `YourBody/Resources/Info.plist` and the built `Info.plist` for `CFBundleExecutable`, `CFBundleIdentifier`, `CFBundleName`, `CFBundlePackageType`, `CFBundleShortVersionString`, and `CFBundleVersion`.
- If launch fails after install, capture recent simulator logs:

  ```bash
  xcrun simctl spawn booted log show --style compact --last 2m \
    --predicate 'process == "SpringBoard" OR eventMessage CONTAINS[c] "com.tacogips.yourbody"'
  ```

- If the app launches but Keychain operations report `-34018`, suspect missing signing entitlements from `CODE_SIGNING_ALLOWED=NO` or manual packaging. Prefer a normally signed simulator build.

## Temporary Smoke Test

Use temporary compromises only when the user explicitly wants immediate visual launch evidence and label the result as non-release verification.

When full asset packaging is blocked by an SDK/runtime mismatch, an asset-excluded Simulator build can confirm Swift compilation and AppIntents metadata without proving icons or asset catalog packaging:

```bash
DERIVED_DATA="/tmp/YourBodyIOSProjectSDKRootNoAssets"
rm -rf "$DERIVED_DATA"
xcodebuild \
  -project YourBody.xcodeproj \
  -target YourBody \
  -sdk iphonesimulator \
  -configuration Debug \
  SYMROOT="$DERIVED_DATA" \
  build \
  EXCLUDED_SOURCE_FILE_NAMES=Assets.xcassets \
  ASSETCATALOG_COMPILER_APPICON_NAME= \
  ASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME= \
  ONLY_ACTIVE_ARCH=NO \
  CODE_SIGNING_ALLOWED=NO
```

If a temporary build produces an installable app and the user wants visual evidence, install and launch it only as a smoke test. Do not present an asset-excluded or signing-disabled launch as release verification. A passing final launch requires the normal `YourBody` scheme build, app resources, entitlements, privacy manifest, StoreKit file, and asset catalog packaging.

## Completion Checklist

Before final response, provide:

- Device and runtime used.
- Build command and pass/fail result.
- Installed bundle identifier.
- Launch PID, if launch succeeded.
- Screenshot path, if captured.
- Verification commands run, including `scripts/verify.sh` and relevant Xcode variants when files changed.
- Exact blocker and classification when launch did not succeed.
