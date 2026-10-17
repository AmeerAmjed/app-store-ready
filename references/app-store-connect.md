# App Store Connect reference

Contents: 1 App Information · 2 Version page · 3 App Privacy · 4 Privacy manifest · 5 Export compliance · 6 Age rating · 7 App Review info · 8 Screenshots · 9 Common rejections · 10 Build & upload

Requirements change; if something here conflicts with what App Store Connect shows the user, trust App Store Connect and say so.

**Direct links** — wherever a report or page names an App Store Connect location ("App Store Connect → App Privacy → Get Started"), make it a link. `<id>` is the app's Apple ID (the number in the URL once the app is open in App Store Connect); ask for it, and fall back to the apps list without it:

| Location | URL |
|---|---|
| Apps list / + New App | `https://appstoreconnect.apple.com/apps` |
| App Information (name, category, Age Ratings) | `https://appstoreconnect.apple.com/apps/<id>/distribution/info` |
| iOS version page (description, keywords, URLs, screenshots, App Review) | `https://appstoreconnect.apple.com/apps/<id>/distribution/ios/version/inflight` |
| App Privacy | `https://appstoreconnect.apple.com/apps/<id>/distribution/privacy` |
| TestFlight | `https://appstoreconnect.apple.com/apps/<id>/testflight/ios` |

## 1. App Information (set once per app)

| Field | Limit / notes |
|---|---|
| Name | ≤30 chars, unique on the store. Can differ from the home-screen `CFBundleDisplayName`. |
| Subtitle | ≤30 chars, localizable. |
| Bundle ID | Must match `PRODUCT_BUNDLE_IDENTIFIER`; register it under Certificates, Identifiers & Profiles first (Xcode automatic signing does this). Cannot be changed after first upload. |
| SKU | Private, any unique string (e.g. `<appname>-ios-001`). |
| Primary language | The language most users see; store metadata falls back to it. |
| Category | Primary + optional secondary (e.g. Business, Finance, Productivity). |
| Content rights | Does the app show third-party content? |
| Age rating | From the questionnaire (section 6). |
| Distribution | Public store, or **unlisted** (link only), or **Apple Business Manager / custom app** for internal company apps. For staff-only apps with admin-created accounts, mention custom/unlisted distribution as an option. |

## 2. Version page (per release, localizable)

- Promotional text ≤170 (editable without review) · Description ≤4000 · Keywords ≤100 chars total, comma-separated, no spaces needed, don't repeat the app name · What's New (not on first version).
- Support URL (required) · Marketing URL (optional) · Privacy Policy URL (required, on App Privacy page) · Copyright (e.g. `2026 Company Name`).
- Build: pick an uploaded build. Version string = `CFBundleShortVersionString` (Flutter: `version: X.Y.Z+N` → X.Y.Z), build = `CFBundleVersion` (N). Each upload needs a higher build number than any previous upload for that version.

## 3. App Privacy ("nutrition label")

App Store Connect → App Privacy → Get Started. Mirror the real screens in reports, in order. Screens recorded from the real form (checked against the live form, Oct 2026):

**Screen 1: Data Collection** — Apple's intro: you're responsible for third-party code in the app, so data your third-party partners collect must be included. "Collect" = transmitting data off the device in a way that allows you and/or your third-party partners to access it for longer than necessary to service the request in real time. "Third-party partners" = analytics tools, advertising networks, third-party SDKs, or other external vendors whose code is in the app.

Question: **Do you or your third-party partners collect data from this app?** — `Yes, we collect data from this app` / `No, we do not collect data from this app`.

How to answer from code: any login, upload or API call that stores user data on a server → Yes. Also Yes if any analytics, crash-reporting or ad SDK is bundled, even if the app's own backend stores nothing. "No" only for apps that send nothing, or only send data that is used once and not stored.

**Per-data-type screens** (purposes, linked to identity, tracking) are not recorded here: which ones appear and how to answer depend on each project's data, so work them out from the code for that app, using the summary below.

"Collected" = transmitted off the device and stored longer than needed to serve the request in real time, by you or any third-party SDK. On-device only data is not collected.

For each type: **Linked to identity?** (tied to an account/device ID) · **Used for tracking?** (linked with other companies' data for ads/data brokers — needs ATT prompt) · **Purposes**: Third-Party Advertising, Developer's Advertising or Marketing, Analytics, Product Personalization, App Functionality, Other.

Data types:
- Contact Info: Name, Email Address, Phone Number, Physical Address, Other User Contact Info
- Health & Fitness: Health, Fitness
- Financial Info: Payment Info, Credit Info, Other Financial Info (e.g. expense amounts, salary)
- Location: Precise Location, Coarse Location
- Sensitive Info
- Contacts
- User Content: Emails or Text Messages, Photos or Videos, Audio Data, Gameplay Content, Customer Support, Other User Content
- Browsing History · Search History
- Identifiers: User ID, Device ID
- Purchases: Purchase History
- Usage Data: Product Interaction, Advertising Data, Other Usage Data
- Diagnostics: Crash Data, Performance Data, Other Diagnostic Data
- Other Data

Typical mappings: account login → User ID (+ Email/Phone if used to sign in); uploaded photos → Photos or Videos; GPS attached to records → Precise Location; a persistent device identifier sent to the server → Device ID (a plain model name like `iPhone16,2` is not); Crashlytics/Sentry → Crash Data, Performance Data; Firebase Analytics → Product Interaction, Device ID (Analytics).

## 4. Privacy manifest (`PrivacyInfo.xcprivacy`)

Required since May 2024 when the app or bundled SDKs call "required reason" APIs: `NSUserDefaults` (reason `CA92.1` app's own data), file timestamp (`C617.1`/`DDA9.1`), system boot time (`35F9.1`), disk space (`E174.1`/`85F4.1`), active keyboards. Also declares `NSPrivacyTracking`, `NSPrivacyTrackingDomains`, `NSPrivacyCollectedDataTypes`. Third-party SDKs on Apple's list must ship their own signed manifest — current Flutter plugins do. Add the app-level file to the Runner target (Xcode: File → New → App Privacy).

Minimal app-level example (adjust collected types to match section 3):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>NSPrivacyTracking</key><false/>
  <key>NSPrivacyTrackingDomains</key><array/>
  <key>NSPrivacyAccessedAPITypes</key>
  <array>
    <dict>
      <key>NSPrivacyAccessedAPIType</key><string>NSPrivacyAccessedAPICategoryUserDefaults</string>
      <key>NSPrivacyAccessedAPITypeReasons</key><array><string>CA92.1</string></array>
    </dict>
  </array>
  <key>NSPrivacyCollectedDataTypes</key>
  <array>
    <dict>
      <key>NSPrivacyCollectedDataType</key><string>NSPrivacyCollectedDataTypePreciseLocation</string>
      <key>NSPrivacyCollectedDataTypeLinked</key><true/>
      <key>NSPrivacyCollectedDataTypeTracking</key><false/>
      <key>NSPrivacyCollectedDataTypePurposes</key><array><string>NSPrivacyCollectedDataTypePurposeAppFunctionality</string></array>
    </dict>
  </array>
</dict>
</plist>
```

## 5. Export compliance (encryption)

Using only HTTPS/TLS, Keychain and other OS-provided crypto, or standard algorithms for authentication/data protection → **exempt**. Add to Info.plist:

```xml
<key>ITSAppUsesNonExemptEncryption</key>
<false/>
```

Custom/proprietary encryption, or encryption as a core feature (VPN, encrypted messaging) → not exempt; may need documentation (and a French declaration if distributing in France). Ask the user if the code suggests this.

## 6. Age Ratings form

App Store Connect → App Information → Age Ratings is a 7-step form. Mirror it exactly in reports: same step names, groups, question wording, and NO/YES or NONE/INFREQUENT/FREQUENT answers, with a one-line reason per answer from the code. All 7 steps recorded from the real form (checked against the live form, Oct 2026):

**Step 1: Features** — "Select whether your app has certain in-app controls, which can be used to limit the content in your app, and capabilities."

| Group | Question | Apple's definition |
|---|---|---|
| In-App Controls | Parental Controls | Settings or tools that allow parents/guardians to monitor, manage or restrict a child's access to in-app content or features that may not be suitable. |
| In-App Controls | Age Assurance | Mechanism to confirm an individual's age meets the age requirement for accessing specific content or services. |
| Capabilities | Unrestricted Web Access | Users can navigate to any webpage within the app or freely browse the web. |
| Capabilities | User-Generated Content | Includes the broad distribution of content created by users as a component of the app's intended user experience. |
| Capabilities | Social Media | Redistribution, amplification, or interaction with user-generated content through a social feed or similar discovery method that visibly spreads content to many users. |
| Capabilities | Social Media Disabled for Users Under 13 | Users under 13 don't have access to social media capabilities. At a minimum, the Declared Age Range API is called to check users' age ranges before enabling social media features. Only age-appropriate UGC is delivered. |
| Capabilities | Messaging and Chat | Users can directly communicate with one another through features within the app. |
| Capabilities | Advertising | Paid promotion of products or services within the app. |

How to answer from code: web view / in-app browser → Unrestricted Web Access; content other users can see (posts, comments, shared media) → User-Generated Content (data sent only to the app's own company/backend is not UGC); feeds → Social Media; user-to-user chat → Messaging; ad SDKs → Advertising.

**Step 2: Mature Themes** — "Select the frequency at which each type of content occurs in your app based on the definitions below. If you have in-app controls, consider what a user who has those turned on will encounter while using your app." Scale: NONE / INFREQUENT (users will rarely encounter this content) / FREQUENT (users will regularly encounter this content).

| Group | Question | Apple's definition |
|---|---|---|
| Mature Themes | Profanity or Crude Humor | Offensive or vulgar language that may be considered rude, obscene, or inappropriate. |
| Mature Themes | Horror/Fear Themes | Content or storylines that evoke feelings of anxiety, dread, or terror. |
| Mature Themes | Alcohol, Tobacco, or Drug Use or References | References to or depictions of the consumption of alcohol, tobacco products, or other licit or illicit substances. |

How to answer from code: only content the app itself shows counts. Fixed UI text in a business/utility app → NONE. Content from users, a feed or a web view can contain any of these, so judge by what's actually reachable in the app.

**Step 3: Medical or Wellness** — same intro and NONE / INFREQUENT / FREQUENT scale as Step 2, followed by a NO / YES question.

| Group | Question | Apple's definition |
|---|---|---|
| Medical or Wellness (frequency) | Medical or Treatment Information | Content that provides diagnoses or guidance around the management of medical conditions or health and wellness. |
| Select if your app has the following (NO/YES) | Health or Wellness Topics | Content that provides self-care or lifestyle recommendations. |

How to answer from code: HealthKit, symptom checkers, medication or treatment content → Medical; fitness, sleep, diet or mindfulness tips → Health or Wellness Topics. Otherwise NONE / NO.

**Step 4: Sexuality or Nudity** — same intro and NONE / INFREQUENT / FREQUENT scale as Step 2.

| Group | Question | Apple's definition |
|---|---|---|
| Sexuality or Nudity | Mature or Suggestive Themes | Content that implies or indirectly references sexual or mature topics without being explicit or topics for older audiences due to the complex, intense, or sensitive nature, which may deal with real-world issues or content unsuitable for children. |
| Sexuality or Nudity | Sexual Content or Nudity | Non-explicit depictions of sexual behavior, including brief or partial nudity. |
| Sexuality or Nudity | Graphic Sexual Content and Nudity | Explicit, detailed depictions of sexual activity or nudity. |

How to answer from code: dating, mature media or unmoderated user photos and web content can reach these; a business/utility app with fixed content → NONE for all three. "Mature or Suggestive Themes" also covers sensitive real-world topics, so news or social-issue content may need INFREQUENT.

**Step 5: Violence** — same intro and NONE / INFREQUENT / FREQUENT scale as Step 2.

| Group | Question | Apple's definition |
|---|---|---|
| Violence | Cartoon or Fantasy Violence | Physical conflict or harm of an exaggerated or fantastical nature that can easily be distinguished from real life. |
| Violence | Realistic Violence | Aggressive physical conflict or harm involving humans in lifelike situations. |
| Violence | Prolonged Graphic or Sadistic Realistic Violence | Prolonged detailed or realistic-looking depictions of physical conflict. |
| Violence | Guns or Other Weapons | References to or depictions of guns, weapons, or objects that may cause bodily harm. |

How to answer from code: games, video/news feeds and hunting, military or security apps can reach these (weapon references alone count for "Guns or Other Weapons"). A business/utility app with fixed content → NONE for all four.

**Step 6: Chance-Based Activities** — same intro and NONE / INFREQUENT / FREQUENT scale as Step 2, followed by NO / YES questions.

| Group | Question | Apple's definition |
|---|---|---|
| Chance-Based Activities (frequency) | Simulated Gambling | Betting or wagering without using real money or in-game currency that can be exchanged for real money. |
| Chance-Based Activities (frequency) | Contests | Events that allow users to compete with one another for rankings, rewards, or the achievement of personal goals. |
| Select if your app has the following (NO/YES) | Gambling | Betting or wagering using real money or in-game currency that may be exchanged for real money. |
| Select if your app has the following (NO/YES) | Loot Boxes | Virtual containers that provide players with randomized virtual items for purchase. |

How to answer from code: casino/slot mechanics without payouts → Simulated Gambling; leaderboards, challenges, streak rewards or competitions between users → Contests (gamified business apps can hit this); real-money betting → Gambling (also needs licensing and geo-restriction); randomized paid items via in-app purchase → Loot Boxes. No games, leaderboards or IAP → NONE / NO.

**Step 7: Additional Information**

- **Calculated Rating** — shown from steps 1–6 ("You can still adjust your app's categorization or increase its rating."). All NONE/NO → 4+.
- **Age Categories and Override** — one of: *Not Applicable* (keep the calculated rating), *Made for Kids* (puts the app in the Kids category with its extra rules: no third-party analytics/ads, parental gates for links and purchases), *Override to Higher Age Rating*. If the app has a EULA with a minimum age, the rating must match that minimum. "Unrated" is for unsuitable content not covered by the previous steps.
- **Age Suitability URL** (optional) — a page with more information about the app's age suitability.

How to answer: Not Applicable unless the app is genuinely built for children (Made for Kids) or its terms require a minimum age (override to match). Leave the URL empty unless such a page exists.

## 7. App Review information

- Sign-in required → demo **username and password** that work against the production server, with sample data, not expiring. If login uses SSO/OTP, explain how the reviewer gets in (or provide a demo mode).
- Contact: first/last name, phone, email (real people Apple can call).
- Notes: what the app is, who uses it, how accounts are provisioned, step-by-step test path, why each permission and background mode is needed, any hardware requirements (e.g. camera — reviewers test on real devices).
- Attachment: optional demo video, useful for hardware/location-dependent flows.

## 8. Screenshots

Required (portrait or landscape, PNG/JPEG, no alpha, 1–10 per size per language):
- iPhone 6.9" — 1320×2868 (or 1290×2796). If 6.9" is provided, smaller iPhone sizes are scaled automatically. 6.5" (1284×2778 / 1242×2688) is accepted if 6.9" isn't.
- iPad 13" — 2064×2752 (or 2048×2732) — required only if the app supports iPad (`TARGETED_DEVICE_FAMILY` contains 2).
Capture from the Simulator (iPhone 16/17 Pro Max for 6.9", iPad Pro 13") with `xcrun simctl io booted screenshot file.png`. App previews (video, 15–30 s) optional.

## 9. Common rejections to pre-empt

- 2.1 App completeness: crashes, broken login, placeholder content, server unreachable, no demo account.
- 2.3 Metadata: screenshots not showing the real app, misleading name/keywords.
- 4.0 Design / 4.2 minimum functionality: wrapped website, iPad layout broken on an iPad-enabled app.
- 5.1.1 Privacy: vague permission strings, collecting data not needed, no privacy policy, no account deletion when sign-up exists, requiring login for features that don't need it.
- 5.1.2: privacy label doesn't match behavior.
- 2.5.4: background modes declared without matching functionality.
- 3.1.1: unlocking digital features without In-App Purchase.
- 3.2 (business): apps for a single company's staff may be rejected from the public store and pushed to Custom App distribution (Apple Business Manager) or Unlisted — choose that up front for internal tools.

## 10. Build & upload

- Flutter: `flutter build ipa --release --dart-define=...` → `build/ios/ipa/*.ipa` and `build/ios/archive/Runner.xcarchive`. Native: Xcode → Product → Archive.
- Upload: Xcode Organizer (Distribute App → App Store Connect), Apple's Transporter app, or `xcrun altool --upload-app` (notarytool is for macOS notarization, not App Store uploads).
- After processing (~10–30 min) the build shows in TestFlight; answer export compliance if not set in Info.plist; test via TestFlight before submitting for review.
