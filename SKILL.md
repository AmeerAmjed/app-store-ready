---
name: app-store-ready
description: Audit an iOS or Flutter project and produce everything needed to submit it to the Apple App Store / App Store Connect — app info, bundle ID, version, signing, permissions, App Privacy "nutrition label" answers inferred from the code, export-compliance (encryption), privacy manifest, age rating, review notes and demo account, screenshots, URLs, localization — as a checklist of what's ready, what's broken, and what the user still has to provide. Use this whenever the user wants to publish, upload, release or submit an app to the App Store, TestFlight or App Store Connect, asks "what do I need for the App Store", "what info does Apple ask for", "prepare for iOS review", or is filling in App Store Connect forms — even if they don't say "checklist".
---

# App Store submission prep

The goal is a single document the user can work through to get from "the app builds" to "submitted for review" without being surprised by an App Store Connect form or a rejection. Most of the answers are already in the code — derive them from there instead of asking. Ask the user only for things that genuinely live outside the repo (marketing copy, URLs, contact details, a reviewer account).

## 1. Gather facts mechanically

Run the scanner from the project root:

```bash
python3 ~/.claude/skills/app-store-ready/scripts/scan_ios.py <project_root>
```

It prints JSON: bundle IDs, versions, deployment target, team/signing, display name, Info.plist usage strings, background modes, ATS, encryption flag, privacy manifest, 1024 icon (and whether it has alpha), localizations, dependencies, http/https URLs found in source, and "signals" (files hinting at login, location, camera, analytics, ads, payments, push, etc.), plus quick warnings.

Also in the JSON: background task ids used in code (compare with `bg_task_identifiers`), iOS plugins that ship no privacy manifest, URLs with the file they came from (comments are skipped), and `git_uncommitted` — if facts come from uncommitted files, say so in the report.

Signals are keyword hits, not proof. Open the listed files to confirm before you state anything about data collection — a wrong App Privacy answer is a real compliance problem, and an over-cautious one scares users away. Also read anything that explains what the app *does* (README, the main screens, API client) so you can describe it accurately to the reviewer.

## 2. Work out the answers

Read `references/app-store-connect.md` for the full list of App Store Connect fields, the App Privacy data categories, the export-compliance decision, age-rating questions, screenshot sizes and the common rejection reasons. Use it to turn the facts into concrete answers:

- **App Privacy**: for each data type the app collects (things that leave the device — sent to your server or a third party), decide: linked to the user? used for tracking? purpose (App Functionality, Analytics, …)? Data that only stays on device is not "collected". Map plugins to data: e.g. location attached to uploads → Precise Location, linked, App Functionality; a login → Email/User ID, linked. Check what is actually *sent*: reading the device model for a session label is not "Device ID" — only a persistent identifier (identifierForVendor, advertising ID, a generated install ID) is.
- **Encryption**: an app that only uses HTTPS/standard OS crypto is exempt → recommend `ITSAppUsesNonExemptEncryption = false` in Info.plist so the question stops appearing on every upload.
- **Privacy manifest** (`PrivacyInfo.xcprivacy`): required when the app or its SDKs use "required reason" APIs (UserDefaults, file timestamps, disk space, system boot time). Most plugins ship their own, but not all — for each entry in `ios_plugins_without_privacy_manifest`, work out which required-reason APIs it uses (e.g. a statically linked SQLite reads file timestamps → `FileTimestamp` / `C617.1`) and declare them in the app-level manifest. Its collected data types must match the App Privacy answers exactly.
- **Reviewer access**: if the app has a login, Apple *will* reject without a working demo account (Guideline 2.1). If the app forces a password change or onboarding on first login, the demo account must have it already done. If accounts are created by an admin (no sign-up in app), say so in review notes — that's also why in-app account deletion (5.1.1(v)) may not apply; if users can sign up, deletion must exist.
- **Permissions**: every `NS…UsageDescription` must clearly say why, in the app's languages; missing strings for a used API crash the app and get rejected. Check each used capability has one, and flag unused ones.
- **Background modes**: each declared mode must be justified — reviewers ask (Guideline 2.5.4), so flag unused ones. Background tasks only run if three things agree: the task id used in code, `BGTaskSchedulerPermittedIdentifiers`, and the native registration (for Flutter workmanager: `WorkmanagerPlugin.registerPeriodicTask(withIdentifier:)` plus `setPluginRegistrantCallback` in AppDelegate). A mismatch fails silently.
- **Build path**: with Swift Package Manager plugins, build with `flutter build ipa` rather than archiving straight from Xcode — some plugins (e.g. `permission_handler`) only get their configuration from the Flutter build.
- **Distribution**: if the app is only for one organization's staff (admin-created accounts, no sign-up, no public value), a public listing risks rejection (Guideline 3.2) — recommend Unlisted or Custom App distribution.
- **Localization**: if the app is localized in code (ARB/strings) but iOS has no `CFBundleLocalizations`/`.lproj` for those languages, iOS and the store treat it as single-language; permission strings should exist in each language.
- **Server**: release builds must point at a reachable `https` backend. Flag `localhost`/LAN/`http` defaults and remind how the production URL is injected (e.g. `--dart-define`).
- **Fit and finish**: 1024 icon without alpha; display name not a package name; version/build bumped above the last upload; iPad support (`TARGETED_DEVICE_FAMILY` includes 2) means iPad screenshots are required and the iPad layout will be reviewed — suggest iPhone-only if the app isn't designed for iPad.

## 3. Write the report

Save it as `APP_STORE_SUBMISSION.md` in the project root (or where the user asks), and write it in the language the user is using with you; keep App Store Connect field names in English so they match the UI. Use this structure:

```markdown
# App Store submission — <App name>

## Status at a glance
✅ ready · ⚠️ needs a fix in the project · ❓ you need to provide · one line each, the blockers first

## Fix before uploading
Numbered, concrete changes in the repo (file + what to change). Offer to make them.

## App Store Connect — App Information
Table: Field | Value (from project or suggested) | Source / status
(Name ≤30, Subtitle ≤30, Bundle ID, SKU, Primary language, Category, Content rights, Age rating)

## Version page
Promotional text, Description, Keywords (≤100 chars), Support URL, Marketing URL, Copyright, Version, Build, What's New.
Draft the description/keywords/subtitle from what the app actually does, in the app's primary language (and others it's localized in), clearly marked as drafts.

## App Privacy (nutrition label)
Table: Data type | Collected? | Linked to user | Tracking | Purpose | Evidence (file)
Then "Privacy Policy URL: ❓" and the tracking answer.

## Age rating answers
Each questionnaire item with the suggested answer.

## Export compliance
Answer + the Info.plist key to add.

## App Review information
Sign-in required? demo username/password ❓ · contact name/phone/email ❓ · draft Review Notes explaining the app, who it's for, how to test it, why each permission and background mode is used.

## Screenshots & media
Required device sizes for this app's device family, which screens to capture, language versions.

## Build & upload
Exact build command for this project (with production config), signing check, upload path (Xcode Organizer / Transporter), TestFlight step.

## What I still need from you
A short list of every ❓ item, so the user can answer in one message.
```

Every value should say where it came from (file path) or be marked as a suggestion — the user needs to know which answers are facts and which are guesses. Don't invent URLs, emails, phone numbers or credentials; leave them as ❓.

Before finishing, re-run `git status` (or the scanner): if the project changed while you worked, update the affected sections rather than handing over a stale report.

## 4. Follow up

After presenting the report, offer to apply the "Fix before uploading" items (e.g. add `ITSAppUsesNonExemptEncryption`, create `PrivacyInfo.xcprivacy`, bump the build number). Once the user answers the ❓ items, update the report in place rather than writing a new one.
