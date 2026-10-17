#!/usr/bin/env python3
"""Scan a Flutter or native iOS project for App Store submission facts.

Usage: python3 scan_ios.py [project_root]

Prints a JSON report of everything that can be read mechanically from the
project (Info.plist, project.pbxproj, pubspec.yaml, icons, privacy manifest,
dependencies, URLs in source). The skill turns this into the human-facing
checklist; this script only gathers facts and never edits anything.
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
SKIP_DIRS = {"build", "Pods", ".dart_tool", ".git", "node_modules", "DerivedData", ".symlinks", "ephemeral"}


def rel(p):
    return os.path.relpath(p, ROOT)


def walk(exts):
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            if f.endswith(exts):
                yield os.path.join(d, f)


def read(p):
    try:
        with open(p, encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except OSError:
        return ""


def plist_json(p):
    try:
        out = subprocess.run(["plutil", "-convert", "json", "-o", "-", p], capture_output=True, text=True, check=True)
        return json.loads(out.stdout)
    except Exception:
        return None


def find_ios_dir():
    for cand in ("ios", "."):
        d = os.path.join(ROOT, cand)
        if any(n.endswith(".xcodeproj") for n in os.listdir(d) if os.path.isdir(os.path.join(d, n))):
            return d
    return None


report = {"project_root": ROOT, "type": None, "warnings": []}
ios = find_ios_dir()
pubspec = os.path.join(ROOT, "pubspec.yaml")
report["type"] = "flutter" if os.path.exists(pubspec) else ("native-ios" if ios else "unknown")
if not ios:
    report["warnings"].append("No .xcodeproj found — is this an iOS project?")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    sys.exit(0)

# --- pubspec (Flutter) -----------------------------------------------------
deps = []
if os.path.exists(pubspec):
    text = read(pubspec)
    m = re.search(r"^version:\s*([^\s#]+)", text, re.M)
    report["pubspec_version"] = m.group(1) if m else None
    m = re.search(r"^description:\s*(.+)$", text, re.M)
    report["pubspec_description"] = m.group(1).strip().strip("\"'") if m else None
    block = re.search(r"^dependencies:\n((?:[ \t]+.*\n|\s*\n)+)", text, re.M)
    if block:
        deps = re.findall(r"^  ([a-zA-Z0-9_]+):", block.group(1), re.M)
    report["dependencies"] = deps

# --- Xcode project -----------------------------------------------------------
proj = next((os.path.join(ios, n, "project.pbxproj") for n in os.listdir(ios) if n.endswith(".xcodeproj")), None)
pbx = read(proj) if proj else ""


def settings(key):
    return sorted(set(v.strip().strip('"') for v in re.findall(rf"\b{key} = ([^;]+);", pbx)))


bundle_ids = settings("PRODUCT_BUNDLE_IDENTIFIER")
report["bundle_ids"] = [b for b in bundle_ids if not b.endswith("Tests")]
report["deployment_targets"] = settings("IPHONEOS_DEPLOYMENT_TARGET")
report["development_team"] = settings("DEVELOPMENT_TEAM")
report["code_sign_style"] = settings("CODE_SIGN_STYLE")
report["device_family"] = settings("TARGETED_DEVICE_FAMILY")
report["swift_package_manager"] = "XCSwiftPackageProductDependency" in pbx
report["cocoapods"] = os.path.exists(os.path.join(ios, "Podfile"))
report["entitlements_files"] = [rel(p) for p in walk((".entitlements",))]

# --- Info.plist ----------------------------------------------------------------
info_path = os.path.join(ios, "Runner", "Info.plist")
if not os.path.exists(info_path):
    info_path = next((p for p in walk(("Info.plist",)) if "Tests" not in p), None)
info = plist_json(info_path) if info_path else None
report["info_plist"] = rel(info_path) if info_path else None
if info:
    report["display_name"] = info.get("CFBundleDisplayName")
    # Flutter resolves these from pubspec `version:` (X.Y.Z+N) at build time.
    report["version_plist"] = info.get("CFBundleShortVersionString")
    report["build_plist"] = info.get("CFBundleVersion")
    report["bundle_name"] = info.get("CFBundleName")
    report["usage_descriptions"] = {k: v for k, v in info.items() if k.endswith("UsageDescription")}
    report["background_modes"] = info.get("UIBackgroundModes", [])
    report["bg_task_identifiers"] = info.get("BGTaskSchedulerPermittedIdentifiers", [])
    report["ats"] = info.get("NSAppTransportSecurity")
    report["uses_non_exempt_encryption"] = info.get("ITSAppUsesNonExemptEncryption", "NOT SET")
    report["supported_orientations"] = info.get("UISupportedInterfaceOrientations", [])
    report["ipad_orientations"] = info.get("UISupportedInterfaceOrientations~ipad", [])
    report["requires_full_screen"] = info.get("UIRequiresFullScreen")
    report["url_schemes"] = [s for t in info.get("CFBundleURLTypes", []) for s in t.get("CFBundleURLSchemes", [])]
    report["localizations_plist"] = info.get("CFBundleLocalizations", [])
    report["dev_region"] = info.get("CFBundleDevelopmentRegion")

# --- Localizations ------------------------------------------------------------
lprojs = sorted({os.path.basename(os.path.dirname(p)).replace(".lproj", "") for p in walk((".strings", ".storyboard", ".xcstrings")) if ".lproj" in p})
arbs = sorted({re.sub(r"^.*_([a-zA-Z_]+)\.arb$", r"\1", p) for p in walk((".arb",))})
report["localizations_lproj"] = lprojs
report["localizations_arb"] = arbs

# --- Privacy manifest -----------------------------------------------------------
manifests = [p for p in walk((".xcprivacy",))]
report["app_privacy_manifest"] = [rel(p) for p in manifests if os.path.dirname(p) == os.path.dirname(info_path or "")]

# --- App icon --------------------------------------------------------------------
icon = None
for p in walk((".png",)):
    if "AppIcon.appiconset" in p and "1024" in os.path.basename(p):
        icon = p
        break
report["app_icon_1024"] = rel(icon) if icon else None
if icon:
    out = subprocess.run(["sips", "-g", "hasAlpha", "-g", "pixelWidth", "-g", "pixelHeight", icon], capture_output=True, text=True).stdout
    report["app_icon_has_alpha"] = "hasAlpha: yes" in out
    m = re.search(r"pixelWidth: (\d+)", out)
    report["app_icon_width"] = int(m.group(1)) if m else None

# --- Source scan: URLs, auth, data signals -----------------------------------------
src_exts = (".dart", ".swift", ".m", ".kt", ".ts", ".js")
urls, http_urls, signals = set(), set(), {}
SIGNALS = {
    "login_auth": r"auth/login|signIn\(|/login\b|FirebaseAuth",
    "account_creation": r"auth/register|/signup|signUp\(|sign_up|createAccount|createUser\(",
    "account_deletion": r"deleteAccount|delete_account|account/delete|destroyAccount",
    "location": r"geolocator|CLLocationManager|getCurrentPosition|latitude",
    "camera_photos": r"\bcamera\b|AVCapture|image_picker|PHPicker|UIImagePicker",
    "contacts": r"contacts_service|CNContact",
    "analytics": r"firebase_analytics|FirebaseAnalytics|mixpanel|amplitude|segment",
    "crash_reporting": r"crashlytics|sentry|bugsnag",
    "ads_tracking": r"google_mobile_ads|AdMob|app_tracking_transparency|ATTrackingManager|IDFA",
    "payments_iap": r"in_app_purchase|StoreKit|revenue_?cat|stripe",
    "push_notifications": r"firebase_messaging|onesignal|UNUserNotificationCenter|registerForRemoteNotifications|aps-environment",
    # Hits mean device info is *read*; check what is actually sent — a model
    # name is not "Device ID" in App Privacy terms, identifierForVendor is.
    "device_info": r"device_info|identifierForVendor|androidId",
    "third_party_login": r"google_sign_in|flutter_facebook_auth|sign_in_with_apple|GIDSignIn",
    "webview": r"webview_flutter|WKWebView",
    "user_generated_content": r"reportContent|report_abuse|blockUser|block_user|chat_message",
}
for p in walk(src_exts):
    if "/test/" in p or p.endswith((".g.dart", ".freezed.dart")) or "/gen/" in p or "GeneratedPluginRegistrant" in p:
        continue
    t = read(p)
    for line in t.splitlines():
        if line.lstrip().startswith(("//", "///", "*", "/*", "#")):
            continue  # doc comments often mention dev URLs that aren't live config
        for u in re.findall(r"https?://[A-Za-z0-9.\-:]+[^\s'\"`)]*", line):
            (http_urls if u.startswith("http://") else urls).add(f"{u}  ({rel(p)})")
    for name, rx in SIGNALS.items():
        if re.search(rx, t, re.I):
            signals.setdefault(name, set()).add(rel(p))
noise = ("flutter.dev", "dart.dev", "pub.dev", "github.com", "apple.com", "android.com", "googleapis.com/auth", "schemas.")
report["https_urls"] = sorted(u for u in urls if not any(n in u for n in noise))[:40]
report["http_urls"] = sorted(u for u in http_urls if not any(n in u for n in noise))[:40]
dep_text = " ".join(deps)
for name, rx in SIGNALS.items():
    if re.search(rx, dep_text, re.I):
        signals.setdefault(name, set()).add("pubspec.yaml")
report["signals"] = {k: sorted(v, key=lambda f: ("table" in f or "model" in f, f))[:10] for k, v in sorted(signals.items())}

# --- Background task ids: Dart/Swift names vs Info.plist permitted list ---------
task_ids = set()
for p in walk((".dart", ".swift", ".m")):
    t = read(p)
    consts = dict(re.findall(r"const\s+(\w+)\s*=\s*'([^']+)'", t))
    for arg in re.findall(r"register(?:PeriodicTask|OneOffTask|ProcessingTask|BGProcessingTask)\s*\(\s*(?:withIdentifier:\s*)?([^,\)]+)", t):
        arg = arg.strip()
        name = arg.strip("'\"") if arg[:1] in "'\"" else consts.get(arg)
        if name:
            task_ids.add(name)
report["background_task_ids_in_code"] = sorted(task_ids)

# --- Flutter iOS plugins without their own privacy manifest -------------------------
deps_file = os.path.join(ROOT, ".flutter-plugins-dependencies")
missing = []
if os.path.exists(deps_file):
    try:
        for plug in json.load(open(deps_file)).get("plugins", {}).get("ios", []):
            if plug.get("dev_dependency"):
                continue  # test-only plugins never ship in the app
            has = any(f.endswith(".xcprivacy") for _, _, fs in os.walk(plug["path"]) for f in fs)
            if not has:
                missing.append(plug["name"])
    except Exception:
        pass
report["ios_plugins_without_privacy_manifest"] = missing

# --- Uncommitted changes (facts may come from work in progress) --------------------
try:
    report["git_uncommitted"] = subprocess.run(["git", "-C", ROOT, "status", "--short"], capture_output=True, text=True).stdout.split("\n")[:30]
except Exception:
    report["git_uncommitted"] = None

# --- Docs that may already hold URLs/contacts -------------------------------------------
report["privacy_policy_mentions"] = sorted({rel(p) for p in walk((".md", ".dart", ".swift", ".html")) if re.search(r"privacy[ _-]?policy", read(p), re.I)})[:10]

# --- Quick warnings ----------------------------------------------------------------
w = report["warnings"]
if report.get("uses_non_exempt_encryption") == "NOT SET":
    w.append("ITSAppUsesNonExemptEncryption not set — App Store Connect will ask about encryption on every upload.")
if not report["app_privacy_manifest"]:
    w.append("No app-level PrivacyInfo.xcprivacy found.")
if report.get("app_icon_has_alpha"):
    w.append("1024 app icon has an alpha channel — App Store rejects it.")
if not report["development_team"]:
    w.append("No DEVELOPMENT_TEAM set — signing not configured.")
if report.get("display_name") and re.search(r"[_]|^[a-z]", report["display_name"]):
    w.append(f"Display name looks like a package name: {report['display_name']!r}")
if "login_auth" in report["signals"] and "account_creation" in report["signals"] and "account_deletion" not in report["signals"]:
    w.append("App lets users create accounts but no in-app account deletion found (Guideline 5.1.1(v)).")

permitted = set(report.get("bg_task_identifiers", []))
for tid in task_ids - permitted:
    w.append(f"Background task {tid!r} is used in code but not in BGTaskSchedulerPermittedIdentifiers — iOS will refuse to schedule it.")
modes = set(report.get("background_modes", []))
if "processing" in modes and not re.search(r"ProcessingTask|BGProcessingTask", " ".join(read(p) for p in walk((".dart", ".swift")))):
    w.append("UIBackgroundModes declares 'processing' but no processing task is registered (Guideline 2.5.4).")
if missing:
    w.append(f"iOS plugins without their own PrivacyInfo.xcprivacy: {', '.join(missing)} — declare their required-reason API use in the app manifest.")
if len(report["localizations_arb"]) > 1 and not report.get("localizations_plist") and len(report["localizations_lproj"]) <= 1:
    w.append("App is localized in Dart but iOS doesn't know it (no CFBundleLocalizations / .lproj) — the store and system UI show only one language.")
if report.get("swift_package_manager") and "permission_handler" in dep_text:
    w.append("permission_handler under Swift Package Manager: build with `flutter build ipa` (not a bare Xcode archive) so its permission macros are applied.")

print(json.dumps(report, indent=2, ensure_ascii=False))
