# app-store-ready

A [Claude Code](https://claude.com/claude-code) skill that gets an iOS or Flutter app ready for App Store review.

It reads your project and tells you what to enter in every App Store Connect form, what's ready, what's broken, and what only you can provide.

## What it covers

- **App information**: name, bundle ID, version, category, signing
- **App Privacy** ("nutrition label"): answers worked out from what your code actually sends off the device
- **Privacy manifest** (`PrivacyInfo.xcprivacy`), including plugins that ship without one
- **Export compliance** (encryption)
- **Age Ratings**, step by step, following Apple's current form
- **Permissions and background modes**: missing or unused usage strings, background-task mismatches
- **App Review**: demo account, review notes, distribution choice
- **Screenshots, URLs, localization**
- **Common rejection reasons**, checked before you submit
- **Build and upload**
- **Direct links** to each App Store Connect page

## Install

```bash
git clone https://github.com/AmeerAmjed/app-store-ready ~/.claude/skills/app-store-ready
```

Restart Claude Code if it was already running.

## Use

In your app's project folder, run:

```
/app-store-ready
```

Or just ask, for example "what do I need for the App Store?" or "help me fill in App Privacy".

## Files

| File | What it does |
|---|---|
| `SKILL.md` | Instructions Claude follows |
| `references/app-store-connect.md` | Apple's App Store Connect forms, fields and rules |
| `scripts/scan_ios.py` | Scans the project for facts (bundle ID, permissions, SDKs, URLs…) and prints JSON |

Requires Python 3 for the scanner. No other dependencies.

## Update

```bash
git -C ~/.claude/skills/app-store-ready pull
```

Apple changes its forms from time to time. If something here doesn't match what App Store Connect shows you, trust App Store Connect, and please open an issue.

## License

[MIT](LICENSE)
