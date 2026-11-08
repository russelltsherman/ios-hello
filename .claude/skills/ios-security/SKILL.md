---
name: ios-security
description: Security rules for this iOS 26 app mapped to OWASP MASVS - secret and credential storage (Keychain), file data protection, network security (ATS), cryptography (CryptoKit), logging without leaking data, deep-link and input validation, and the privacy manifest. Use when code handles tokens, passwords, keys, personal data, files, network configuration, URLs from outside the app, logging, or Info.plist / entitlements / PrivacyInfo.xcprivacy changes, and when reviewing code for security.
---

# iOS Security

Map every finding to an OWASP MASVS control group so reviews are consistent: STORAGE, CRYPTO, AUTH, NETWORK,
PLATFORM, CODE, RESILIENCE, PRIVACY. Verify the current MASVS version at https://mas.owasp.org before citing
control IDs; this skill names groups only.

Build-setting hardening (compiler warnings, Enhanced Security, pointer authentication) is covered by Apple's
`audit-xcode-security-settings` skill, installed with `scripts/install-apple-skills`. This skill covers app code.

## Hard rules

| MASVS | Rule |
|---|---|
| STORAGE | Tokens, passwords, keys and refresh secrets go in the Keychain. Never `UserDefaults`, `@AppStorage`, plist, Core Data/SwiftData, or files. |
| STORAGE | Every Keychain item sets `kSecAttrAccessible` explicitly. Default to `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly` (or `WhenUnlockedThisDeviceOnly` if never needed in the background). Never the deprecated `kSecAttrAccessibleAlways*`. |
| STORAGE | Files containing personal data are written with `.completeFileProtection` (or `.completeFileProtectionUnlessOpen` when written in the background). |
| CRYPTO | Use CryptoKit. Never write your own crypto, never use ECB/CBC without authentication, never hard-code keys or IVs. |
| NETWORK | HTTPS only. Never add `NSAllowsArbitraryLoads` or per-domain ATS exceptions without a written justification in the PR. |
| CODE | Validate every value from outside the process (deep links, universal links, pasteboard, push payloads, server JSON) before use. |
| CODE | No secrets in source, `Info.plist`, `.xcconfig` or asset catalogs. Anything shipped in the bundle is public. |
| PRIVACY | Never log tokens, credentials or personal data. Mark interpolations in `Logger` with an explicit privacy level. |
| PRIVACY | Any use of a required-reason API (e.g. `UserDefaults`, file timestamps, disk space, system boot time) must be declared in `PrivacyInfo.xcprivacy` with an approved reason code. |

## Keychain: generic password item

Check every `OSStatus`. Update first, then add if the item is missing. Treat "not found" on delete as success. This
implementation is tested in `evals/tasks/token` (save, replace, load, clear, idempotent clear).

```swift
import Foundation
import Security

enum KeychainError: Error, Equatable {
    case unexpectedStatus(OSStatus)
    case invalidData
}

struct KeychainItem: Sendable {
    let service: String
    let account: String

    func save(_ secret: String) throws(KeychainError) {
        let attributes: [CFString: Any] = [
            kSecValueData: Data(secret.utf8),
            kSecAttrAccessible: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly,
        ]
        let status = SecItemUpdate(query() as CFDictionary, attributes as CFDictionary)
        switch status {
        case errSecSuccess:
            return
        case errSecItemNotFound:
            let addStatus = SecItemAdd(query().merging(attributes) { $1 } as CFDictionary, nil)
            guard addStatus == errSecSuccess else { throw .unexpectedStatus(addStatus) }
        default:
            throw .unexpectedStatus(status)
        }
    }

    func load() throws(KeychainError) -> String? {
        var request = query()
        request[kSecReturnData] = true
        request[kSecMatchLimit] = kSecMatchLimitOne
        var result: CFTypeRef?
        let status = SecItemCopyMatching(request as CFDictionary, &result)
        switch status {
        case errSecSuccess:
            guard let data = result as? Data, let secret = String(data: data, encoding: .utf8) else {
                throw .invalidData
            }
            return secret
        case errSecItemNotFound:
            return nil
        default:
            throw .unexpectedStatus(status)
        }
    }

    func delete() throws(KeychainError) {
        let status = SecItemDelete(query() as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else { throw .unexpectedStatus(status) }
    }

    private func query() -> [CFString: Any] {
        [kSecClass: kSecClassGenericPassword, kSecAttrService: service, kSecAttrAccount: account]
    }
}
```

Notes:
- Keychain calls are synchronous and can block. Call them off the main actor (e.g. from a `nonisolated` service).
- `errSecInteractionNotAllowed` means the device is locked and the accessibility class forbids access. Surface it
  as "try again later". Do not retry in a loop, and do not downgrade the accessibility class.
- Keychain items have historically persisted after app deletion (observed behavior, not a documented guarantee).
  If a fresh install must start signed out, clear items on first launch and don't rely on deletion doing it.
- In Swift package tests on the iOS simulator without a host app, Keychain calls fail with `-34018`
  (missing entitlement). Test Keychain code from an app-hosted test target or on the macOS host.

## File protection

```swift
import Foundation

func writeHealthExport(_ data: Data, to url: URL) throws {
    try data.write(to: url, options: [.atomic, .completeFileProtection])
}
```

Exclude caches of personal data from backups with `URLResourceValues.isExcludedFromBackup` when they can be
regenerated.

## CryptoKit

Use `AES.GCM` or `ChaChaPoly` for symmetric encryption. A fresh random nonce is generated per `seal` call, so do not
supply your own unless a protocol requires it. Store keys in the Keychain; never derive them from a password with a
plain hash (use a KDF such as HKDF for key material, and server-side password hashing for passwords).

```swift
import CryptoKit
import Foundation

func encrypt(_ plaintext: Data, using key: SymmetricKey) throws -> Data? {
    try AES.GCM.seal(plaintext, using: key).combined
}

func decrypt(_ combined: Data, using key: SymmetricKey) throws -> Data {
    try AES.GCM.open(AES.GCM.SealedBox(combined: combined), using: key)
}
```

`combined` is optional only for nonstandard nonce sizes. With the default nonce it is non-nil, but handle `nil`
rather than force-unwrapping.

## Logging

```swift
import os

let authLog = Logger(subsystem: "com.example.app", category: "auth")

func logSignIn(userID: String, attempt: Int) {
    authLog.info("Sign-in for \(userID, privacy: .private(mask: .hash)) attempt \(attempt, privacy: .public)")
}
```

Never interpolate tokens, passwords or full request bodies into logs, even at `.debug`. Never use `print` for
diagnostics in shipping code.

## Deep links and external input

Parse into a closed enum, and reject anything that doesn't match. Never pass URL components straight into file
paths, web views, or SQL/predicate strings.

```swift
import Foundation

enum DeepLink: Equatable {
    case product(id: Int)
    case settings
}

func parseDeepLink(_ url: URL) -> DeepLink? {
    guard url.scheme == "myapp", let components = URLComponents(url: url, resolvingAgainstBaseURL: false) else {
        return nil
    }
    switch components.host {
    case "settings":
        return .settings
    case "product":
        guard let raw = components.queryItems?.first(where: { $0.name == "id" })?.value,
            let id = Int(raw), id > 0
        else { return nil }
        return .product(id: id)
    default:
        return nil
    }
}
```

## Privacy manifest

- Every target that ships code (app, extensions, frameworks) needs a `PrivacyInfo.xcprivacy` when it uses
  required-reason APIs or collects data.
- Declare each required-reason API category with the reason code that matches the actual use. Look up current
  categories and codes in Apple's "Describing use of required reason API" documentation. Do not guess codes.
- Declare tracking domains and collected data types honestly. A mismatch with App Store Connect privacy labels is a
  review risk.

## Security review checklist

- [ ] No secrets in UserDefaults, plists, files, logs, source or bundle (search for `token`, `password`, `secret`, `apiKey`).
- [ ] Every `SecItem*` status is checked; accessibility is explicit and `ThisDeviceOnly` unless syncing is required.
- [ ] Personal-data files use complete file protection.
- [ ] No ATS exceptions, or each one is justified.
- [ ] External inputs are parsed into closed types and validated.
- [ ] `Logger` interpolations of user data are `.private`.
- [ ] `PrivacyInfo.xcprivacy` is updated for any new required-reason API or data collection.
