# iOS App Integration Guide

**Complete reference for integrating with Arca Backend Firebase Functions**

Last updated: 2025-10-19
Backend Project: `arca-baf77`
Region: `us-central1`

---

## Getting Started (New Developers)

**Complete this checklist before starting development:**

### 1. Get Firebase Configuration
- [ ] Contact backend team to get `GoogleService-Info.plist` for project `arca-baf77`
- [ ] Add `GoogleService-Info.plist` to Xcode project root
- [ ] Ensure the plist is added to your app target

### 2. Install Dependencies
- [ ] Add Firebase SDK via CocoaPods or Swift Package Manager:
  ```ruby
  # Podfile
  pod 'Firebase/Auth'
  pod 'Firebase/Functions'
  pod 'Firebase/Firestore'
  pod 'GoogleSignIn'  # For Google Sign-In
  ```
  Or SPM: Add `https://github.com/firebase/firebase-ios-sdk`

### 3. Configure Firebase in Your App
- [ ] Initialize Firebase in `AppDelegate` or `@main`:
  ```swift
  import Firebase

  FirebaseApp.configure()
  ```

### 4. Set Up Authentication
- [ ] Enable Apple Sign-In in Xcode (Signing & Capabilities)
- [ ] Configure Google Sign-In (get OAuth client ID from Firebase Console)
- [ ] Implement auth flow (see [Authentication](#authentication) section)

### 5. Configure Functions Region
- [ ] Set functions region to `us-central1`:
  ```swift
  let functions = Functions.functions(region: "us-central1")
  ```

### 6. Development: Connect to Emulator (Optional)
- [ ] For local testing, add emulator configuration for DEBUG builds:
  ```swift
  #if DEBUG
  Functions.functions(region: "us-central1").useEmulator(withHost: "127.0.0.1", port: 5001)
  #endif
  ```

### 7. Test the Integration
- [ ] Create test user with Apple/Google Sign-In
- [ ] Call `get_sun_sign_from_date()` with a test date
- [ ] Call `create_user_profile()` with test user credentials
- [ ] Verify profile creation in Firebase Console

### 8. Test User for Analytics Filtering
**Important**: Use these test credentials to avoid polluting production analytics:
- **User ID**: `integration_test_user`
- **Name**: `Alex`
- **Email**: `alex@test.com`
- **Birth Date**: `1990-06-15` (Gemini)

This test user is excluded from analytics on the backend.

---

## Table of Contents

1. [Overview](#overview)
2. [Firebase Setup](#firebase-setup)
3. [Available Functions](#available-functions)
4. [User Onboarding Flow](#user-onboarding-flow)
5. [Daily Horoscope Flow](#daily-horoscope-flow)
6. [Data Models](#data-models)
7. [Error Handling](#error-handling)
8. [Testing](#testing)
9. [Analytics](#analytics)
10. [Background Tasks & Notifications](#background-tasks--notifications)

---

## Overview

The Arca backend is built on **Firebase Cloud Functions (Python 3.13)** with **Firestore** as the database. All functions are **callable functions** - you call them via the Firebase SDK, not REST endpoints.

### App & Audience Brief

**Product:**
A daily tarot and astrology app powered by AI that provides personalized spiritual guidance for navigating real-life situations and decisions. Using an LLM, the app delivers tailored readings and derives deep personalization including recurring themes, evolving insights, and pattern recognition across your journey.

**Target Audience:**
- **Demographics**: Women, 18-35 years old, iPhone users, mass market appeal (accessible pricing)
- **Psychographics**: Navigating relationships, dating, career decisions, friendships, and life transitions. Seeking guidance and clarity about everyday situations. Use spirituality as a framework for understanding their lives. Drawn to astrology, tarot, manifestation content (Co-Star, TikTok spirituality). Value aesthetics and aspirational content. Want to feel understood and validated.
- **Core Need**: A daily companion for processing life's questions—relationships, work, identity—through a spiritual lens that makes them feel purposeful rather than anxious.

**Brand Positioning:**
- **The Tension**: Users want accessible, practical guidance for real problems (love, work, life choices) BUT want to feel like they're on an elevated spiritual journey, not just "fixing problems."
- **How We Position**:
  - **Elevated, never transactional** - This is a sacred practice, not a problem-solving tool
  - **Transformational framing** - Everyday concerns are reframed as spiritual evolution and inner work
  - **Personal and intimate** - "Your journey," "your truest self," personalized to YOU
  - **Ancient wisdom meets daily life** - Timeless practices for modern living
  - **Aspirational but accessible** - Everyone can be a spiritual seeker
- **The Promise**: Transform daily life situations into opportunities for self-discovery and growth through personalized spiritual guidance.
- **What We're NOT**: Cheap fortune-telling app, transactional advice column, superficial entertainment, elite/gatekept spiritual practice
- **What We ARE**: Your personal spiritual companion that helps you navigate real life with ancient wisdom, intention, and deeper self-understanding.

**Technology & Personalization:**
- **LLM-driven readings** - Each reading is uniquely generated based on your specific situation and energy
- **Theme tracking** - The app identifies and surfaces recurring themes in your journey (e.g., boundaries, self-worth, career courage)
- **Evolving insights** - Guidance deepens and adapts as the app learns your patterns and growth areas
- **Pattern recognition** - Connects dots across readings to show you how situations and lessons relate
- **Journey documentation** - Creates a living record of your spiritual evolution with synthesized insights over time
- **The AI Advantage** (never explicitly stated to users): The personalization feels mystical and intuitive, like the app "knows you" deeply—but it's powered by sophisticated pattern recognition and contextual understanding that makes ancient practices feel alive and responsive to modern life.

### Product Roadmap

**V1 (MVP)**:
- Sun sign + transits horoscope
- 8 life categories (see below for descriptions)
- Personalized per user with memory tracking
- Journal entries track reading behavior
- Apple/Google authentication

**V2**:
- Full natal chart integration (exact birth time required)
- House-based predictions
- Aspect interpretations
- Rising sign and Moon sign integration
- More precise personalization

**V3**:
- Q&A interface with tarot card readings
- Multi-card spreads
- Conversational spiritual guidance
- Journal expands to include tarot readings and reflections
- Pattern recognition across entries begins
- **Push Notifications**: Daily horoscope notifications using `daily_theme_headline`
  - Background fetch using BackgroundTasks framework (BGAppRefreshTask)
  - Local notification scheduling
  - Precomputed horoscope caching
  - Notification preferences and timing
  - See [Background Tasks & Notifications](#background-tasks--notifications) for implementation details

**V4**:
- Synthesized insights about recurring themes
- Long-term spiritual journey tracking
- Automated pattern detection
- Personalized growth recommendations

**Later (Post-V4)**:
- **Premium Subscriptions**: In-app purchases via StoreKit
  - Subscription tiers and pricing
  - StoreKit 2 integration
  - Receipt validation
  - Premium feature gating
  - Free trial management
  - Note: `is_premium` and `premium_expiry` fields in User Profile are prepared for future use

### The 8 Life Categories

All horoscope predictions are organized into these categories:

| Category | Icon | Description | Field Name |
|----------|------|-------------|------------|
| **Love & Relationships** | 💕 | Romance, dating, partnerships, emotional state with significant other. Includes finding a partner, improving relationships, healing from breakups, compatibility, communication, commitment. | `love_relationships` |
| **Family & Friendships** | 👥 | Platonic and familial relationships. Interpersonal dynamics with family and friends, healing rifts, communication, family patterns, boundaries, parenting, sibling dynamics. | `family_friendships` |
| **Path & Profession** | 💼 | Career, work, education, life path. Job changes, career direction, professional development, workplace dynamics, finding fulfilling vocation, entrepreneurship. | `path_profession` |
| **Personal Growth & Well-being** | 🌱 | Self-improvement, self-awareness, emotional healing, mental health, physical well-being, shadow work, habits, overcoming obstacles. Internal state and personal development. | `personal_growth` |
| **Finance & Abundance** | 💰 | Money, wealth, financial stability, investments, material resources, money mindset. Improving financial situation, managing debt, financial decisions, relationship with money. | `finance_abundance` |
| **Life Purpose & Spirituality** | ✨ | Deeper meaning, destiny, soul's journey, spiritual gifts, karmic lessons, ancestral wisdom, psychic development, connection to universe/higher power. | `purpose_spirituality` |
| **Home & Environment** | 🏡 | Living situations, moving, relocating, home purchases, creating harmonious spaces, roommate dynamics, impact of physical environment on wellbeing. | `home_environment` |
| **Decisions & Crossroads** | 🔀 | Making choices between options, understanding outcomes, clarity at major turning points, determining timing. Functional category for discernment in any life area. | `decisions_crossroads` |

**Note**: Each category receives ~100-120 words of detailed guidance in the horoscope.

### Architecture

- **Two-Prompt Architecture**: Horoscopes are generated in 2 stages for optimal UX
  - **Prompt 1 (Daily)**: Fast core analysis, shown immediately (<2s target)
  - **Prompt 2 (Detailed)**: Deep predictions per category, loaded in background (~5-10s)

- **Journal → Memory Pattern**:
  - Journal entries are immutable source of truth
  - Memory collection is derivative cache updated via Firestore triggers
  - Memory is accessible via `get_memory()` function (primarily for debugging/analytics)

### Key Principles

1. **No real-time listeners** - All data is fetched on-demand via callable functions
2. **Background triggers** - Memory updates happen automatically via Firestore triggers
3. **Birth Chart Modes** (user data level, not app version):
   - **Sun Sign Mode**: Birth date only → Sun sign + approximate chart (`mode: "v1"`)
   - **Natal Chart Mode**: Full birth info → Precise natal chart with houses/angles (`mode: "v2"`)
   - Note: These data modes are independent of the app's release versions (V1, V2, V3, V4)

### Offline Support & Caching Strategy

**Problem**: Users opening the app without internet connection (subway, airplane, poor signal) will see nothing.

**Solution**: Implement local caching for graceful offline experience.

**What to Cache:**

1. **Sun Sign Profile** (`get_sun_sign_from_date` response)
   - Cache: **ALWAYS** - This is static data that never changes
   - Invalidate: Never (birth date → sun sign is deterministic)
   - Storage: UserDefaults
   - Key: `cached_sunsign_{birth_date}`
   - **Saves bandwidth** - No need to call backend more than once per birth date

2. **User Profile** (`create_user_profile` response)
   - Cache: On successful profile creation and updates
   - Invalidate: Never (profile rarely changes)
   - Storage: UserDefaults

3. **Daily Horoscope** (`get_daily_horoscope` response)
   - Cache: On successful fetch with today's date
   - Invalidate: When date changes (midnight)
   - Storage: UserDefaults with date
   - Key: `cached_horoscope_{date}_{userId}`
   - **Valid for today only** - Don't fetch multiple times same day

4. **Detailed Horoscope** (`get_detailed_horoscope` response)
   - Cache: On successful fetch with today's date
   - Invalidate: When date changes (midnight)
   - Storage: UserDefaults with date
   - Key: `cached_details_{date}_{userId}`
   - **Valid for today only** - Don't fetch multiple times same day

5. **Journal Entries** (App Release V3+)
   - Cache: All journal entries locally (create offline, sync when online)
   - Invalidate: Never (immutable once created)
   - Storage: Local database (CoreData, Realm, or SQLite)
   - **Previous horoscopes accessible through journal** - Not cached separately

6. **Insights** (App Release V4+)
   - Cache: Most recent insights and synthesized themes
   - Storage: Local database with timestamp

**Sun Sign Lookup (Always Check Cache First):**

```swift
func getSunSign(birthDate: String) async throws -> SunSignProfile {
    // Check cache first (saves bandwidth!)
    let cacheKey = "cached_sunsign_\(birthDate)"
    if let cached = UserDefaults.standard.data(forKey: cacheKey),
       let profile = try? JSONDecoder().decode(SunSignProfile.self, from: cached) {
        // Return cached - this never changes
        return profile
    }

    // Not cached - fetch from backend once
    let data: [String: Any] = ["birth_date": birthDate]
    let result = try await functions.httpsCallable("get_sun_sign_from_date").call(data)

    guard let data = result.data as? [String: Any],
          let profileData = data["profile"] as? [String: Any],
          let jsonData = try? JSONSerialization.data(withJSONObject: profileData),
          let profile = try? JSONDecoder().decode(SunSignProfile.self, from: jsonData) else {
        throw NSError(domain: "AppError", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid profile data"])
    }

    // Cache forever (static data)
    if let encoded = try? JSONEncoder().encode(profile) {
        UserDefaults.standard.set(encoded, forKey: cacheKey)
    }

    return profile
}
```

**Horoscope Fetch Logic:**

```swift
func loadDailyHoroscope() async {
    let today = Calendar.current.startOfDay(for: Date())
    let cacheKey = "cached_horoscope_\(userId)"

    // Check if we have today's horoscope cached
    if let cached = loadCachedHoroscope(),
       Calendar.current.isDate(cached.date, inSameDayAs: today) {
        // Already have today's horoscope - show it (no fetch needed)
        displayHoroscope(cached, isOffline: false)
        return
    }

    // Need to fetch new horoscope (date changed or no cache)
    if isOnline {
        // Fetch fresh horoscope
        do {
            let horoscope = try await fetchHoroscopeFromBackend()
            // Save to cache
            self.cacheHoroscope(horoscope)
            self.displayHoroscope(horoscope, isOffline: false)
        } catch {
            self.handleError(error)
        }
    } else {
        // Offline and date changed - show "no connection" state
        self.showOfflineState()
    }
}

func displayHoroscope(_ horoscope: DailyHoroscope, isOffline: Bool) {
    self.summaryLabel.text = horoscope.summary
    // No offline indicator needed - we show same-day cache seamlessly
}

func showOfflineState() {
    // Show when offline AND date changed (no valid cache)
    self.emptyStateView.show(
        icon: "🌙",
        title: "No connection with the moon",
        message: "Your daily horoscope will appear when you're back online.\n\nPrevious readings are available in your journal."
    )
}
```

**Cache Invalidation:**

```swift
func checkCacheValidity() {
    let today = Calendar.current.startOfDay(for: Date())

    // Clear horoscope cache if it's from a previous day
    if let cached = loadCachedHoroscope(),
       !Calendar.current.isDate(cached.date, inSameDayAs: today) {
        clearHoroscopeCache()
    }

    // Sun sign cache is NEVER cleared (static data)
}
```

**Journal Entry Offline Sync (V3+):**

```swift
func createJournalEntry(entry: JournalEntry) async {
    // Always write locally first
    await localDatabase.save(entry)

    // Try to sync to Firestore if online
    if isOnline {
        do {
            try await syncJournalEntry(entry)
            await entry.markAsSynced()
        } catch {
            await entry.markAsPendingSync()
        }
    } else {
        await entry.markAsPendingSync()
    }
}
```

**UX Guidelines:**

1. **Same day = Show cached horoscope** - Don't fetch multiple times per day, saves bandwidth
2. **Different day + online = Fetch fresh** - Clear old cache, get new horoscope
3. **Different day + offline = Show "No connection with the moon"** - Friendly message
4. **No offline indicator for same-day cache** - Seamless UX, user doesn't need to know
5. **Empty state message**:
   ```
   🌙 No connection with the moon

   Your daily horoscope will appear when you're back online.

   Previous readings are available in your journal.
   ```
6. **Sun sign lookup always checks cache first** - Saves bandwidth, never expires
7. **Journal stores historical horoscopes** (V3+) - Access past readings there, not via cache

**Cache Expiration Rules:**

- **Sun sign profiles**: Never expire (static data, bandwidth saver)
- **Horoscopes**: Valid until date changes (same day = use cache, don't refetch)
- **Journal entries**: Never expire (immutable historical data, V3+)
- **Insights**: Until new insights generated (V4+)
- **User profile**: Until explicitly updated

**Performance Benefits:**

- **Reduced bandwidth** - Sun sign profiles cached forever, horoscopes cached same-day
- **Faster app experience** - No unnecessary refetches on same day
- **Graceful degradation** - Clear message when offline and date changed
- **Historical access via journal** (V3+) - Previous horoscopes stored as journal entries

---

## Firebase Setup

### 1. Install Firebase SDK

```swift
// Add to your Podfile or SPM
pod 'Firebase/Functions'
pod 'Firebase/Firestore'
pod 'Firebase/Auth'
```

### 2. Initialize Firebase

```swift
import Firebase

// In AppDelegate or @main
FirebaseApp.configure()

// Get functions reference
let functions = Functions.functions(region: "us-central1")
```

### 3. Authentication

**Required**: Users must authenticate via Firebase Auth to get a permanent `user_id`.

#### Authentication Options (2nd Onboarding Screen)

Per MVP spec, offer two options:

1. **Continue with Apple** (recommended)
2. **Continue with Google**

**DO NOT use anonymous authentication** - users will lose all data if they delete the app or switch devices.

**Data Capture**: During sign-in, you MUST capture:
- ✅ **User name** (always required)
- ✅ **Email** (optional - Apple may hide it if user chooses "Hide My Email")

These are passed to `create_user_profile()` after authentication.

```swift
import Firebase
import AuthenticationServices
import GoogleSignIn

// Option 1: Sign in with Apple
func signInWithApple() {
    let provider = ASAuthorizationAppleIDProvider()
    let request = provider.createRequest()
    request.requestedScopes = [.fullName, .email]

    // Present authorization controller
    let controller = ASAuthorizationController(authorizationRequests: [request])
    controller.delegate = self
    controller.presentationContextProvider = self
    controller.performRequests()
}

// Handle Apple Sign In callback
func authorizationController(controller: ASAuthorizationController,
                            didCompleteWithAuthorization authorization: ASAuthorization) {
    guard let appleIDCredential = authorization.credential as? ASAuthorizationAppleIDCredential else {
        return
    }

    guard let nonce = currentNonce,
          let appleIDToken = appleIDCredential.identityToken,
          let idTokenString = String(data: appleIDToken, encoding: .utf8) else {
        return
    }

    let credential = OAuthProvider.credential(
        withProviderID: "apple.com",
        idToken: idTokenString,
        rawNonce: nonce
    )

    Auth.auth().signIn(with: credential) { authResult, error in
        guard let user = authResult?.user else { return }

        let userId = user.uid
        // Name: Always capture from Apple (required)
        let name = appleIDCredential.fullName?.givenName ?? "User"
        // Email: May be hidden by Apple (empty string if hidden)
        let email = appleIDCredential.email ?? user.email ?? ""

        // Create user profile with captured name and email
        self.createUserProfile(userId: userId, name: name, email: email)
    }
}

// Option 2: Sign in with Google
func signInWithGoogle() {
    guard let clientID = FirebaseApp.app()?.options.clientID else { return }

    let config = GIDConfiguration(clientID: clientID)
    GIDSignIn.sharedInstance.configuration = config

    GIDSignIn.sharedInstance.signIn(withPresenting: self) { result, error in
        guard let user = result?.user,
              let idToken = user.idToken?.tokenString else {
            return
        }

        let credential = GoogleAuthProvider.credential(
            withIDToken: idToken,
            accessToken: user.accessToken.tokenString
        )

        Auth.auth().signIn(with: credential) { authResult, error in
            guard let user = authResult?.user else { return }

            let userId = user.uid
            // Name: Always available from Google
            let name = user.displayName ?? "User"
            // Email: Always available from Google
            let email = user.email ?? ""

            // Create user profile with captured name and email
            self.createUserProfile(userId: userId, name: name, email: email)
        }
    }
}

// Get current authenticated user ID
var currentUserId: String? {
    return Auth.auth().currentUser?.uid
}
```

#### Data Persistence

With Apple/Google sign-in:
- ✅ User keeps same `user_id` across devices
- ✅ All data (profile, journal, natal chart) persists forever
- ✅ User can reinstall app and data is restored
- ✅ Supports multiple devices with same account

#### Security Note (App Release V1)

⚠️ **The backend currently does NOT validate authentication tokens** - it trusts the `user_id` parameter sent by the client. This is acceptable for app release V1 but means:
- iOS app MUST handle auth properly and only send the authenticated user's ID
- Don't allow users to specify arbitrary user IDs
- Firestore security rules are currently in dev mode (expires Nov 15, 2025)

#### Security Roadmap

**App Release V2**: Server-side auth validation
- Add `req.auth` validation in all Cloud Functions
- Verify authenticated user matches requested `user_id`
- Return 403 Forbidden for unauthorized access

**App Release V3**: Push Notifications
- Implement APNS (Apple Push Notification Service)
- Register device tokens with Firebase Cloud Messaging
- Backend sends daily notifications using `daily_theme_headline`
- User preferences for notification timing and frequency

**App Release V3+**: App Check integration
- Implement Firebase App Check to verify requests come from legitimate iOS app
- Protect against:
  - Unauthorized API access from non-app clients
  - Replay attacks
  - Quota abuse
- Add App Check enforcement to all callable functions:
  ```swift
  // iOS implementation (V3+)
  AppCheck.appCheck().setAppCheckProviderFactory { _ in
      return AppAttestProvider(app: FirebaseApp.app()!)
  }
  ```

**Production**: Hardened Firestore rules
- Replace dev mode rules with production security rules
- Enforce user-level data isolation
- Restrict memory collection to server-side only access
- Add rate limiting and abuse prevention

---

## Available Functions

All functions are in region: **us-central1**

### Function List

| Function | Purpose | Speed | Requires Auth |
|----------|---------|-------|---------------|
| `get_sun_sign_from_date` | Calculate sun sign from birth date | <1s | No |
| `create_user_profile` | Create user with natal chart | <2s | Yes |
| `get_user_profile` | Fetch user profile | <1s | Yes |
| `get_daily_horoscope` | Generate daily horoscope (Prompt 1) | <10s | Yes |
| `get_detailed_horoscope` | Generate detailed predictions (Prompt 2) | 10-20s | Yes |
| `add_journal_entry` | Save user reading to journal | <1s | Yes |
| `get_memory` | Fetch memory collection (debugging/analytics) | <1s | Yes |

---

## User Onboarding Flow

### Step 1: Get Sun Sign (Pre-Profile)

Call this during onboarding to show user their sun sign before profile creation.

```swift
func getSunSign(birthDate: String) async throws -> (sunSign: String, profile: [String: Any]) {
    let data: [String: Any] = [
        "birth_date": birthDate  // YYYY-MM-DD format
    ]

    let result = try await functions.httpsCallable("get_sun_sign_from_date").call(data)

    guard let data = result.data as? [String: Any],
          let sunSign = data["sun_sign"] as? String,
          let profile = data["profile"] as? [String: Any] else {
        throw NSError(domain: "AppError", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid sun sign data"])
    }

    // profile contains full sun sign data:
    // - sign: "Gemini"
    // - symbol: "The Twins"
    // - element: "air"
    // - modality: "mutable"
    // - ruling_planet: "Mercury"
    // - keywords: ["Communicative", "Curious", ...]
    // - summary: "Gemini, the third sign..."
    // + 40+ more fields (see functions/signs/*.json)

    return (sunSign, profile)
}

// Usage:
Task {
    do {
        let (sunSign, profile) = try await getSunSign(birthDate: "1990-06-15")
        // Display profile to user
    } catch {
        // Handle error
    }
}
```

**Response Structure:**
```json
{
  "sun_sign": "gemini",
  "profile": {
    "sign": "Gemini",
    "symbol": "The Twins",
    "element": "air",
    "modality": "mutable",
    "ruling_planet": "Mercury",
    "keywords": ["Communicative", "Curious", "Adaptable"],
    "summary": "Gemini, the third sign of the zodiac...",
    "domain_profiles": {
      "love_and_relationships": { ... },
      "family_and_friendships": { ... },
      // ... 8 life domains total
    }
    // ... 40+ more fields
  }
}
```

### Step 2: Create User Profile

Call this after user completes onboarding.

**Sun Sign Mode (Birth Date Only):**
```swift
func createUserProfile(userId: String, name: String, email: String, birthDate: String) async throws -> (success: Bool, sunSign: String, mode: String, exactChart: Bool) {
    let data: [String: Any] = [
        "user_id": userId,
        "name": name,
        "email": email,
        "birth_date": birthDate
    ]

    let result = try await functions.httpsCallable("create_user_profile").call(data)

    guard let data = result.data as? [String: Any] else {
        throw NSError(domain: "AppError", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid profile data"])
    }

    let success = data["success"] as? Bool ?? false
    let sunSign = data["sun_sign"] as? String ?? ""  // "gemini"
    let mode = data["mode"] as? String ?? ""  // "v1"
    let exactChart = data["exact_chart"] as? Bool ?? false  // false

    return (success, sunSign, mode, exactChart)
}

// Usage:
Task {
    do {
        let userId = Auth.auth().currentUser!.uid
        let result = try await createUserProfile(
            userId: userId,
            name: "User Name",
            email: "user@example.com",
            birthDate: "1990-06-15"
        )
        // Profile created successfully
    } catch {
        // Handle error (see Error Handling section)
    }
}
```

**Natal Chart Mode (Full Birth Info):**
```swift
func createUserProfileFull(
    userId: String,
    name: String,
    email: String,
    birthDate: String,
    birthTime: String,
    birthTimezone: String,
    birthLat: Double,
    birthLon: Double
) async throws -> (success: Bool, sunSign: String, mode: String, exactChart: Bool) {
    let data: [String: Any] = [
        "user_id": userId,
        "name": name,
        "email": email,
        "birth_date": birthDate,
        "birth_time": birthTime,  // HH:MM format (in local timezone)
        "birth_timezone": birthTimezone,  // IANA timezone (see note below)
        "birth_lat": birthLat,
        "birth_lon": birthLon
    ]

    let result = try await functions.httpsCallable("create_user_profile").call(data)

    guard let data = result.data as? [String: Any] else {
        throw NSError(domain: "AppError", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid profile data"])
    }

    // Same response structure, but:
    // mode = "v2"  (API returns "v1" or "v2" for backward compatibility)
    // exact_chart = true

    let success = data["success"] as? Bool ?? false
    let sunSign = data["sun_sign"] as? String ?? ""
    let mode = data["mode"] as? String ?? ""  // "v2"
    let exactChart = data["exact_chart"] as? Bool ?? false  // true

    return (success, sunSign, mode, exactChart)
}
```

**Timezone Input (Natal Chart Mode):**

The `birth_timezone` parameter requires an IANA timezone string (e.g., "America/New_York", "Europe/London", "Asia/Tokyo").

**Recommended approach**: Derive timezone from coordinates
```swift
import CoreLocation

func getTimezone(latitude: Double, longitude: Double) async throws -> String {
    let location = CLLocation(latitude: latitude, longitude: longitude)
    let geocoder = CLGeocoder()

    let placemarks = try await geocoder.reverseGeocodeLocation(location)

    guard let timezone = placemarks.first?.timeZone else {
        throw NSError(domain: "AppError", code: -1, userInfo: [NSLocalizedDescriptionKey: "Could not determine timezone"])
    }

    return timezone.identifier  // e.g., "America/New_York"
}

// Usage:
Task {
    do {
        let timezone = try await getTimezone(latitude: 40.7128, longitude: -74.0060)
        // Use timezone for birth_timezone parameter
    } catch {
        // Handle error
    }
}
```

**Alternative approach**: Present timezone picker
- Use `TimeZone.knownTimeZoneIdentifiers` to get all IANA timezones
- Filter by region or search
- Example:
```swift
let allTimezones = TimeZone.knownTimeZoneIdentifiers
// ["Africa/Abidjan", "Africa/Accra", "America/New_York", ...]

// Filter by region
let americanTimezones = allTimezones.filter { $0.hasPrefix("America/") }
```

**Best UX**: Let user select birth location on a map → derive both coordinates AND timezone automatically.

**What happens on the backend:**
1. Validates input
2. Calculates sun sign
3. Computes natal chart (Sun Sign Mode: approximate, Natal Chart Mode: precise)
4. Saves to `users/{userId}` in Firestore
5. Initializes empty memory collection in `memory/{userId}`
6. Returns success + metadata

---

## Daily Horoscope Flow

### Step 1: Get Daily Horoscope (Prompt 1)

**Show this immediately on main screen** - it's fast (<10s).

**Note on `daily_theme_headline`**: This field is designed for push notifications (V3+). Example: "✨ The universe is clearing your path today" - perfect for daily notification copy.

```swift
struct DailyHoroscope {
    let date: String
    let sunSign: String
    let headline: String
    let summary: String
    let technicalAnalysis: String
    let keyTransit: String
    let areaActivated: String
    let lunarUpdate: String
    let advice: ActionableAdvice
    let astrometers: AllMetersReading  // NEW: Complete meter readings with trends
}

struct ActionableAdvice {
    let doThis: String
    let avoid: String
    let affirmation: String
}

func getDailyHoroscope(userId: String, date: String? = nil, modelName: String = "gemini-2.5-flash-lite") async throws -> DailyHoroscope {
    var data: [String: Any] = ["user_id": userId]
    if let date = date {
        data["date"] = date
    }
    data["model_name"] = modelName

    let result = try await functions.httpsCallable("get_daily_horoscope").call(data)

    guard let horoscope = result.data as? [String: Any] else {
        throw NSError(domain: "AppError", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid horoscope data"])
    }

    // Parse fields
    let headline = horoscope["daily_theme_headline"] as? String ?? ""
    let summary = horoscope["summary"] as? String ?? ""
    let technicalAnalysis = horoscope["technical_analysis"] as? String ?? ""
    let keyTransit = horoscope["key_active_transit"] as? String ?? ""
    let areaActivated = horoscope["area_of_life_activated"] as? String ?? ""
    let lunarUpdate = horoscope["lunar_cycle_update"] as? String ?? ""

    // Parse actionable advice
    let adviceDict = horoscope["actionable_advice"] as? [String: Any] ?? [:]
    let advice = ActionableAdvice(
        doThis: adviceDict["do"] as? String ?? "",
        avoid: adviceDict["avoid"] as? String ?? "",
        affirmation: adviceDict["affirmation"] as? String ?? ""
    )

    return DailyHoroscope(
        date: horoscope["date"] as? String ?? "",
        sunSign: horoscope["sun_sign"] as? String ?? "",
        headline: headline,
        summary: summary,
        technicalAnalysis: technicalAnalysis,
        keyTransit: keyTransit,
        areaActivated: areaActivated,
        lunarUpdate: lunarUpdate,
        advice: advice
    )
}

// Usage:
Task {
    do {
        let userId = Auth.auth().currentUser!.uid
        let horoscope = try await getDailyHoroscope(userId: userId)
        // Display on main screen
    } catch {
        // Handle error
    }
}
```

**Response Structure:**
```json
{
  "date": "2025-10-19",
  "sun_sign": "gemini",
  "technical_analysis": "Astronomical explanation...",
  "key_active_transit": "Technical analysis with degrees...",
  "area_of_life_activated": "Life domain being spotlighted...",
  "lunar_cycle_update": "Ritual and wellness guidance...",
  "daily_theme_headline": "Short mystical headline for push notification",
  "daily_overview": "Core insight for main screen...",
  "summary": "Longer summary for main screen...",
  "actionable_advice": {
    "do": "Specific action to take today",
    "avoid": "What to be cautious of",
    "affirmation": "Affirmation for the day"
  },
  "astrometers": {
    "date": "2025-10-19T00:00:00",
    "aspect_count": 34,
    "overall_unified_score": 49.0,
    "overall_unified_quality": "mixed",
    "overall_intensity": {
      "meter_name": "overall_intensity",
      "unified_score": 49.0,
      "unified_quality": "mixed",
      "intensity": 56.3,
      "harmony": 48.2,
      "state_label": "Lively Mix",
      "trend": "worsening",  // NEW: "improving", "stable", or "worsening"
      "interpretation": "This meter shows how much cosmic energy...",
      "advice": ["Advice 1", "Advice 2"]
    },
    // ... 22 more individual meters (all with trend field)
    // ... 5 super-group aggregate meters (also with trend field)
  },
  "model_used": "gemini-2.5-flash-lite",
  "generation_time_ms": 9255,
  "usage": { ... }
}
```

**NEW in October 2025: Trend Analysis**

All 28 meters (23 individual + 5 super-groups) now include a `trend` field that shows how each area is changing compared to yesterday:
- `"improving"` - Quality/harmony increasing (↑ green in UI)
- `"stable"` - No significant change (→ blue in UI)
- `"worsening"` - Quality/harmony decreasing (↓ red in UI)

This allows you to show users not just the current state, but whether things are getting better or worse.

### Step 2: Get Detailed Horoscope (Prompt 2)

**Load this in the background** while user reads the summary. Show when ready (~10-20s).

```swift
struct DetailedHoroscope {
    let overview: [String]
    let lookAhead: String
    let categories: HoroscopeCategories
}

struct HoroscopeCategories {
    let loveRelationships: String
    let familyFriendships: String
    let pathProfession: String
    let personalGrowth: String
    let financeAbundance: String
    let purposeSpirituality: String
    let homeEnvironment: String
    let decisionsCrossroads: String
}

func getDetailedHoroscope(
    userId: String,
    dailyHoroscope: [String: Any],  // REQUIRED: Full result from Prompt 1
    date: String? = nil,
    modelName: String = "gemini-2.5-flash-lite"
) async throws -> DetailedHoroscope {
    var data: [String: Any] = [
        "user_id": userId,
        "daily_horoscope": dailyHoroscope  // REQUIRED
    ]
    if let date = date {
        data["date"] = date
    }
    data["model_name"] = modelName

    let result = try await functions.httpsCallable("get_detailed_horoscope").call(data)

    guard let detailed = result.data as? [String: Any],
          let details = detailed["details"] as? [String: Any] else {
        throw NSError(domain: "AppError", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid detailed horoscope data"])
    }

    // Parse 8 life categories (each is a string with 80-120 words)
    let categories = HoroscopeCategories(
        loveRelationships: details["love_relationships"] as? String ?? "",
        familyFriendships: details["family_friendships"] as? String ?? "",
        pathProfession: details["path_profession"] as? String ?? "",
        personalGrowth: details["personal_growth"] as? String ?? "",
        financeAbundance: details["finance_abundance"] as? String ?? "",
        purposeSpirituality: details["purpose_spirituality"] as? String ?? "",
        homeEnvironment: details["home_environment"] as? String ?? "",
        decisionsCrossroads: details["decisions_crossroads"] as? String ?? ""
    )

    return DetailedHoroscope(
        overview: detailed["general_transits_overview"] as? [String] ?? [],
        lookAhead: detailed["look_ahead_preview"] as? String ?? "",
        categories: categories
    )
}

// Usage (load in background):
Task {
    do {
        let userId = Auth.auth().currentUser!.uid

        // First get daily horoscope
        let dailyHoroscope = try await getDailyHoroscope(userId: userId)
        // Display daily horoscope immediately

        // Then load detailed in background
        let detailed = try await getDetailedHoroscope(
            userId: userId,
            dailyHoroscope: dailyHoroscope  // Pass as parameter
        )
        // Display categories when ready
    } catch {
        // Handle error
    }
}
```

**Response Structure:**
```json
{
  "general_transits_overview": [
    "Brief note on collective transit 1",
    "Brief note on collective transit 2"
  ],
  "look_ahead_preview": "Upcoming significant transits...",
  "details": {
    "love_relationships": "Detailed prediction (80-120 words)...",
    "family_friendships": "Detailed prediction (80-120 words)...",
    "path_profession": "Detailed prediction (80-120 words)...",
    "personal_growth": "Detailed prediction (80-120 words)...",
    "finance_abundance": "Detailed prediction (80-120 words)...",
    "purpose_spirituality": "Detailed prediction (80-120 words)...",
    "home_environment": "Detailed prediction (80-120 words)...",
    "decisions_crossroads": "Detailed prediction (80-120 words)..."
  },
  "model_used": "gemini-2.5-flash-lite",
  "generation_time_ms": 14365,
  "usage": { ... }
}
```

### Step 3: Save Journal Entry

Call this when user reads categories. **This triggers memory update automatically.**

```swift
struct CategoryView {
    let category: String
    let text: String
}

func addJournalEntry(
    userId: String,
    date: String,
    summaryViewed: String,
    categoriesViewed: [CategoryView],
    timeSpentSeconds: Int
) async throws -> (success: Bool, entryId: String) {
    // Convert categories to dictionary format
    let categoriesData = categoriesViewed.map { category in
        [
            "category": category.category,
            "text": category.text
        ]
    }

    let data: [String: Any] = [
        "user_id": userId,
        "date": date,
        "entry_type": "horoscope_reading",
        "summary_viewed": summaryViewed,
        "categories_viewed": categoriesData,
        "time_spent_seconds": timeSpentSeconds
    ]

    let result = try await functions.httpsCallable("add_journal_entry").call(data)

    guard let responseData = result.data as? [String: Any] else {
        throw NSError(domain: "AppError", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid journal entry response"])
    }

    let success = responseData["success"] as? Bool ?? false
    let entryId = responseData["entry_id"] as? String ?? ""

    return (success, entryId)
}

// Usage:
Task {
    do {
        let userId = Auth.auth().currentUser!.uid

        // Track which categories the user expanded and read
        let categoriesViewed = [
            CategoryView(category: "love_relationships", text: loveText),
            CategoryView(category: "path_profession", text: careerText)
        ]

        let (success, entryId) = try await addJournalEntry(
            userId: userId,
            date: "2025-10-19",
            summaryViewed: summaryText,
            categoriesViewed: categoriesViewed,
            timeSpentSeconds: 180  // Track engagement time
        )

        // Journal entry saved, memory will update automatically via trigger
    } catch {
        // Handle error
    }
}
```

**What happens on the backend:**
1. Journal entry saved to `users/{userId}/journal/{entryId}`
2. **Firestore trigger fires automatically** → `update_memory_on_journal_entry`
3. Memory collection updated in `memory/{userId}`:
   - Category view counts incremented
   - Recent readings updated (FIFO, max 10)
   - `updated_at` timestamp updated

### Optional: Get Memory (Debugging/Analytics)

**Note**: This function is primarily for debugging and analytics. The iOS app doesn't need to call it during normal operation - memory is used automatically by the backend for LLM personalization.

```swift
struct MemoryCollection {
    let categories: [String: CategoryMemory]
    let recentReadings: [Reading]
}

struct CategoryMemory {
    let count: Int
    let lastMentioned: String?
}

struct Reading {
    let date: String
    let summary: String
    let categoriesViewed: [CategoryView]
}

func getMemory(userId: String) async throws -> MemoryCollection {
    let data: [String: Any] = ["user_id": userId]

    let result = try await functions.httpsCallable("get_memory").call(data)

    guard let memory = result.data as? [String: Any],
          let categoriesData = memory["categories"] as? [String: Any],
          let readingsData = memory["recent_readings"] as? [[String: Any]] else {
        throw NSError(domain: "AppError", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid memory data"])
    }

    // Parse categories
    var categories: [String: CategoryMemory] = [:]
    for (key, value) in categoriesData {
        if let categoryData = value as? [String: Any] {
            categories[key] = CategoryMemory(
                count: categoryData["count"] as? Int ?? 0,
                lastMentioned: categoryData["last_mentioned"] as? String
            )
        }
    }

    // Parse recent readings
    let readings = readingsData.compactMap { reading -> Reading? in
        guard let date = reading["date"] as? String,
              let summary = reading["summary"] as? String,
              let categoriesViewed = reading["categories_viewed"] as? [[String: Any]] else {
            return nil
        }

        let categories = categoriesViewed.compactMap { cat -> CategoryView? in
            guard let category = cat["category"] as? String,
                  let text = cat["text"] as? String else {
                return nil
            }
            return CategoryView(category: category, text: text)
        }

        return Reading(date: date, summary: summary, categoriesViewed: categories)
    }

    return MemoryCollection(categories: categories, recentReadings: readings)
}

// Usage:
Task {
    do {
        let userId = Auth.auth().currentUser!.uid
        let memory = try await getMemory(userId: userId)

        // Display user's category engagement stats
        for (category, data) in memory.categories {
            print("\(category): \(data.count) views")
        }
    } catch {
        // Handle error
    }
}
```

**Use cases:**
- Display user's category engagement stats
- Show reading history
- Analytics/metrics for premium features

---

## Data Models

All response structures are defined by Pydantic models in the backend. Here are the complete structures you'll receive.

### Category Names

Use these exact strings when reading/writing categories:

```swift
enum Category: String {
    case loveRelationships = "love_relationships"
    case familyFriendships = "family_friendships"
    case pathProfession = "path_profession"
    case personalGrowth = "personal_growth"
    case financeAbundance = "finance_abundance"
    case purposeSpirituality = "purpose_spirituality"
    case homeEnvironment = "home_environment"
    case decisionsCrossroads = "decisions_crossroads"
}
```

### Sun Sign Profile Structure

Returned by `get_sun_sign_from_date()`:

```typescript
{
  sun_sign: string;  // "gemini", "aries", etc.
  profile: {
    // Core identification
    sign: string;  // "Gemini"
    dates: string;  // "May 21 - June 20"
    symbol: string;  // "The Twins"
    glyph: string;  // "♊︎"

    // Elemental classification
    element: "fire" | "earth" | "air" | "water";
    modality: "cardinal" | "fixed" | "mutable";
    polarity: string;  // "Masculine/Yang" or "Feminine/Yin"

    // Planetary rulership
    ruling_planet: string;  // "Mercury", "Venus", etc.
    ruling_planet_glyph: string;  // "☿", "♀", etc.
    planetary_dignities: {
      detriment: string;  // Planet in detriment
      exaltation: string;  // Planet exalted
      fall: string;  // Planet in fall
    };

    // Physical & symbolic correspondences
    body_parts_ruled: string[];  // ["Nervous System", "Lungs", ...]
    correspondences: {
      colors: string[];  // ["Yellow", "Light Green", ...]
      gemstones: string[];  // ["Agate", "Citrine", ...]
      metal: string;  // "Mercury/Quicksilver"
      tarot: string;  // "The Lovers"
      day_of_week: string;  // "Wednesday"
      lucky_numbers: number[];  // [3, 5, 7]
    };

    // Core characteristics
    keywords: string[];  // ["Communicative", "Curious", ...]
    positive_traits: string[];  // ["Intellectually Agile", ...]
    shadow_traits: string[];  // ["Superficial", "Inconsistent", ...]
    life_lesson: string;  // "To find wisdom in facts..."
    evolutionary_goal: string;  // "To become a master of synthesis..."

    // Context & stories
    mythology: string;  // Long description of mythological stories
    seasonal_association: string;  // Connection to natural cycles
    archetypal_roles: string[];  // ["The Messenger", "The Storyteller", ...]
    summary: string;  // Concise overview (2-3 paragraphs)

    // Health & wellness
    health_tendencies: {
      strengths: string;
      vulnerabilities: string;
      wellness_advice: string;
    };

    // Compatibility
    compatibility_overview: {
      most_compatible: Array<{
        sign: string;
        reason: string;
      }>;
      challenging: Array<{
        sign: string;
        reason: string;
      }>;
      growth_oriented: Array<{
        sign: string;
        reason: string;
      }>;
      same_sign: string;
    };

    // 8 life domain profiles
    domain_profiles: {
      love_and_relationships: {
        style: string;
        needs: string;
        gives: string;
        attracts: string;
        challenges: string;
        communication_style: string;
      };
      family_and_friendships: {
        friendship_style: string;
        family_role: string;
        sibling_dynamics: string;
        parenting_style: string;
        childhood_needs: string;
      };
      path_and_profession: {
        work_style: string;
        career_strengths: string[];
        ideal_work_environment: string;
        leadership_approach: string;
        growth_area: string;
      };
      personal_growth_and_wellbeing: {
        stress_triggers: string;
        stress_relief_practices: string;
        growth_path: string;
        mindfulness_approach: string;
        healing_modalities: string[];
      };
      finance_and_abundance: {
        money_mindset: string;
        earning_style: string;
        spending_patterns: string;
        abundance_lesson: string;
        financial_advisory_note: string;
      };
      life_purpose_and_spirituality: {
        spiritual_path: string;
        soul_mission: string;
        connection_to_divine: string;
        spiritual_practices: string[];
      };
      home_and_environment: {
        home_needs: string;
        decorating_style: string;
        location_preferences: string;
        relationship_to_space: string;
        seasonal_home_adjustments: string;
      };
      decisions_and_crossroads: {
        decision_making_style: string;
        when_stuck: string;
        crisis_response: string;
        decision_tips: string;
        advice_for_major_choices: string;
      };
    };
  };
}
```

### Daily Horoscope Structure

Returned by `get_daily_horoscope()` (Prompt 1):

```typescript
{
  date: string;  // "2025-10-19"
  sun_sign: string;  // "gemini"

  // Core fields (in order of presentation)
  technical_analysis: string;  // Astronomical explanation (3-5 sentences)
  key_active_transit: string;  // Technical analysis with exact degrees (4-5 sentences)
  area_of_life_activated: string;  // Life domain spotlighted (2-3 sentences)
  lunar_cycle_update: string;  // Ritual and wellness guidance (3-4 sentences)

  // Display fields
  daily_theme_headline: string;  // Short profound wisdom (max 15 words)
  daily_overview: string;  // Emotional/energetic tone (2-3 sentences)
  summary: string;  // Main screen summary (2-3 sentences)

  // Actionable guidance
  actionable_advice: {
    do: string;  // Specific action aligned with transit
    dont: string;  // Specific thing to avoid
    reflect_on: string;  // Journaling question for self-awareness
  };

  // Metadata
  model_used: string;  // "gemini-2.5-flash-lite"
  generation_time_ms: number;  // 9255
  usage: {
    prompt_token_count: number;
    candidates_token_count: number;
    total_token_count: number;
  };
}
```

### Detailed Horoscope Structure

Returned by `get_detailed_horoscope()` (Prompt 2):

```typescript
{
  // Collective context
  general_transits_overview: string[];  // 2-4 bullet points about collective transits
  look_ahead_preview: string;  // Upcoming significant transits (2-3 sentences)

  // 8 detailed category predictions
  details: {
    love_relationships: string;  // ~100-120 words
    family_friendships: string;  // ~100-120 words
    path_profession: string;  // ~100-120 words
    personal_growth: string;  // ~100-120 words
    finance_abundance: string;  // ~100-120 words
    purpose_spirituality: string;  // ~100-120 words
    home_environment: string;  // ~100-120 words
    decisions_crossroads: string;  // ~100-120 words
  };

  // Metadata
  model_used: string;  // "gemini-2.5-flash-lite"
  generation_time_ms: number;  // 14365
  usage: { ... };
}
```

### User Profile Structure

Stored in Firestore: `users/{userId}`

```typescript
{
  // Identity
  user_id: string;  // Firebase Auth user ID
  name: string;  // User's name from auth provider
  email: string;  // User's email from auth provider

  // Subscription (Post-V4 - prepared for future premium features)
  is_premium: boolean;  // true if user has premium subscription (always false in V1-V4)
  premium_expiry: string | null;  // ISO date or null if non-premium (always null in V1-V4)

  // Birth information
  birth_date: string;  // "1990-06-15" (YYYY-MM-DD)
  birth_time: string | null;  // "14:30" (HH:MM) - optional
  birth_timezone: string | null;  // "America/New_York" (IANA) - optional
  birth_lat: number | null;  // 40.7128 - optional
  birth_lon: number | null;  // -74.0060 - optional

  // Computed data
  sun_sign: string;  // "gemini"
  natal_chart: { ... };  // Complete NatalChartData from astro module
  exact_chart: boolean;  // true if birth_time + timezone provided

  // Timestamps
  created_at: string;  // ISO datetime "2025-10-19T..."
  last_active: string;  // ISO datetime "2025-10-19T..."
}
```

### Journal Entry Structure

Stored in Firestore: `users/{userId}/journal/{entryId}`

```typescript
{
  entry_id: string;  // Auto-generated Firestore document ID
  date: string;  // "2025-10-19" (ISO date)
  entry_type: "horoscope_reading";  // Entry type (only horoscope_reading in app release V1)
  summary_viewed: string;  // The summary text from daily horoscope
  categories_viewed: Array<{
    category: string;  // "love_relationships", "path_profession", etc.
    text: string;  // Full text that was viewed
  }>;
  time_spent_seconds: number;  // Total time spent reading (in seconds)
  created_at: string;  // ISO datetime "2025-10-19T..."
}
```

### Memory Collection Structure

Stored in Firestore: `memory/{userId}` (server-side, accessible via `get_memory()`)

```typescript
{
  user_id: string;  // Firebase Auth user ID

  // Category engagement tracking
  categories: {
    love_relationships: {
      count: number;  // Total times viewed (e.g., 5)
      last_mentioned: string | null;  // ISO date "2025-10-19" or null
    };
    family_friendships: {
      count: number;
      last_mentioned: string | null;
    };
    path_profession: {
      count: number;
      last_mentioned: string | null;
    };
    personal_growth: {
      count: number;
      last_mentioned: string | null;
    };
    finance_abundance: {
      count: number;
      last_mentioned: string | null;
    };
    purpose_spirituality: {
      count: number;
      last_mentioned: string | null;
    };
    home_environment: {
      count: number;
      last_mentioned: string | null;
    };
    decisions_crossroads: {
      count: number;
      last_mentioned: string | null;
    };
  };

  // Recent readings (FIFO queue, max 10)
  recent_readings: Array<{
    date: string;  // "2025-10-19"
    summary: string;  // Summary text shown on main screen
    categories_viewed: Array<{
      category: string;
      text: string;
    }>;
  }>;

  // Timestamp
  updated_at: string;  // ISO datetime "2025-10-19T..."
}
```

---

## Error Handling

All functions return Firebase callable function errors. Handle them using Swift's error handling:

```swift
func callFunction() async {
    do {
        let result = try await functions.httpsCallable("function_name").call(data)
        // Process result
    } catch let error as NSError {
        let code = FunctionsErrorCode(rawValue: error.code)
        let message = error.localizedDescription

        switch code {
        case .invalidArgument:
            // Missing or invalid parameters
            // e.g., "Missing required parameter: user_id"
            print("Invalid input: \(message)")

        case .notFound:
            // Resource not found
            // e.g., "User profile not found: {userId}"
            print("Not found: \(message)")

        case .unauthenticated:
            // User not authenticated
            print("Please sign in")

        case .internal:
            // Server error
            print("Server error: \(message)")

        default:
            print("Error: \(message)")
        }
    }
}
```

### Common Errors

| Error Code | Cause | Solution |
|------------|-------|----------|
| `INVALID_ARGUMENT` | Missing/invalid parameter | Check parameter format |
| `NOT_FOUND` | User profile doesn't exist | Call `create_user_profile` first |
| `UNAUTHENTICATED` | User not signed in | Authenticate via Firebase Auth |
| `INTERNAL` | Server error (LLM, DB, etc.) | Retry or contact support |

### Function-Specific Errors

**`get_detailed_horoscope`**:
- **INVALID_ARGUMENT**: "Missing required parameters: user_id, daily_horoscope"
  - Cause: The `daily_horoscope` parameter was omitted
  - Solution: Always pass the complete result from `get_daily_horoscope()` (Prompt 1)
  - Note: The function does NOT regenerate the daily horoscope internally - it requires it as input

**`create_user_profile`**:
- **INVALID_ARGUMENT**: "Missing required parameters: user_id, name, email, birth_date"
  - Cause: One or more required parameters missing (birth_date is always required)
  - Solution: Ensure all required fields are provided

**`add_journal_entry`**:
- **INVALID_ARGUMENT**: "Missing required parameters: user_id, date, entry_type"
  - Cause: Missing core journal entry fields
  - Solution: Provide all required parameters including categories_viewed array

---

## Testing

### Test User

For analytics filtering, use this test user ID:

```swift
let TEST_USER_ID = "integration_test_user"
let TEST_NAME = "Alex"
let TEST_EMAIL = "alex@test.com"
let TEST_BIRTH_DATE = "1990-06-15"  // Gemini
```

### Production Functions URL

All functions are deployed at:
```
https://us-central1-arca-baf77.cloudfunctions.net/{function_name}
```

### Testing Locally (Emulator)

1. Start Firebase emulator:
   ```bash
   cd arca-backend
   firebase emulators:start
   ```

2. Connect iOS app to emulator:
   ```swift
   #if DEBUG
   Functions.functions().useEmulator(withHost: "127.0.0.1", port: 5001)
   Firestore.firestore().useEmulator(withHost: "127.0.0.1", port: 8080)
   #endif
   ```

3. Run integration test:
   ```bash
   python integration_test.py
   ```

---

## Analytics

### PostHog Integration

The backend logs all LLM requests to PostHog with the following properties:

```json
{
  "distinct_id": "user_id",
  "generation_type": "daily_horoscope" | "detailed_horoscope",
  "model_used": "gemini-2.5-flash-lite",
  "generation_time_ms": 9255,
  "input_tokens": 5000,
  "output_tokens": 1200,
  "total_tokens": 6200
}
```

This is **server-side only** - no iOS integration needed.

### Test User Filtering

Filter out test users in PostHog using:
```
user_id != "integration_test_user"
```

---

## Function Call Sequence

### Typical User Flow

```
1. Onboarding:
   get_sun_sign_from_date → create_user_profile

2. Daily Check-In:
   get_daily_horoscope (show immediately)
   ↓
   get_detailed_horoscope (load in background)
   ↓
   User reads categories
   ↓
   add_journal_entry
   ↓
   [Trigger fires automatically] → update_memory_on_journal_entry

3. Repeat Daily:
   get_daily_horoscope → get_detailed_horoscope → add_journal_entry
```

### Memory Update Flow

```
iOS App                Backend                    Firestore
   |                      |                           |
   |--add_journal_entry-->|                           |
   |                      |--write to users/journal-->|
   |<--success-----------|                           |
   |                      |                           |
   |                      |    [Trigger fires]        |
   |                      |<--journal created---------|
   |                      |                           |
   |                      |--read memory collection-->|
   |                      |--update memory counts---->|
   |                      |                           |
```

**Important**: The memory update happens **asynchronously** via trigger. The iOS app doesn't need to wait for it - just save the journal entry and move on.

---

## Performance Reality (Measured Data)

**Benchmark results from production using `gemini-2.5-flash-lite` (10 iterations per function):**

| Function | Target | **Median (Actual)** | **P95** | Success Rate | Status | Notes |
|----------|--------|---------------------|---------|--------------|--------|-------|
| `get_sun_sign_from_date` | <1s | **644ms** | 1151ms | 100% | 🟢 | Fast enough |
| `create_user_profile` | <2s | **757ms** | 1693ms | 100% | 🟢 | One-time call, acceptable |
| `get_daily_horoscope` | <2s | **5419ms (5.4s)** | 8220ms | 100% | 🟡 | **2.7x slower than target** |
| `get_detailed_horoscope` | 5-10s | **9909ms (9.9s)** | 11944ms | 90% | 🟡 | 1/10 timeout >120s |
| `add_journal_entry` | <500ms | **665ms** | 1475ms | 100% | 🟢 | Fast enough |
| `get_memory` | <500ms | **723ms** | 1725ms | 100% | 🟢 | Fast enough |

**Model Used**: `gemini-2.5-flash-lite` (cost-optimized, lowest latency)

### Critical Finding: Main Screen Loading

**`get_daily_horoscope` median: 5.4 seconds (P95: 8.2 seconds)**

This is the CRITICAL path for the main screen. Users will experience:
- **Median case**: ~5.4 second wait
- **Worst case (P95)**: ~8.2 second wait
- **2.7x slower** than the <2s target

**`get_detailed_horoscope` median: 9.9 seconds (P95: 11.9 seconds)**
- 90% success rate (1/10 requests timeout after 120 seconds)
- Load in background while user reads summary

### Loading State UX (REQUIRED)

**DO NOT show a blank screen or simple spinner for 5-10 seconds.** Users will think the app is broken.

**Recommended: Skeleton Loader with Mystical Messages**

```swift
func loadDailyHoroscope() async {
    // Show skeleton + mystical loading message
    summaryView.showSkeleton(lines: 3, animated: true)

    let messages = [
        "✨ Consulting the cosmos...",
        "🌙 Reading the moon's position...",
        "⭐ Interpreting planetary alignments...",
        "💫 Finalizing your reading..."
    ]

    let messageTask = Task {
        await showRotatingMessage(messages, interval: 2.0)
    }

    // Fetch horoscope (expect 5-10 seconds)
    do {
        let horoscope = try await fetchDailyHoroscope()
        messageTask.cancel()
        summaryView.hideSkeleton()
        displayHoroscope(horoscope)
    } catch {
        messageTask.cancel()
        summaryView.hideSkeleton()
        handleError(error)
    }
}
```

**Alternative: Progressive Text Reveal**

```swift
func loadDailyHoroscope() async {
    // Show loading state with progressive messages
    let loadingStates = [
        (0, "✨ Consulting the cosmos..."),
        (2, "🌙 Analyzing lunar positions..."),
        (4, "⭐ Interpreting planetary alignments..."),
        (6, "💫 Almost there...")
    ]

    let messageTask = Task {
        for (delay, message) in loadingStates {
            try? await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
            await MainActor.run {
                self.loadingLabel.text = message
            }
        }
    }

    do {
        let horoscope = try await fetchDailyHoroscope()
        messageTask.cancel()
        // Display after 5+ seconds
        self.displayHoroscope(horoscope)
    } catch {
        messageTask.cancel()
        handleError(error)
    }
}
```

### Timeout Handling (30 seconds)

```swift
func fetchDailyHoroscope(userId: String, timeout: TimeInterval = 30) async throws -> DailyHoroscope {
    let data: [String: Any] = ["user_id": userId]

    return try await withThrowingTaskGroup(of: DailyHoroscope.self) { group in
        // Add the actual request task
        group.addTask {
            let result = try await self.functions.httpsCallable("get_daily_horoscope").call(data)
            guard let horoscope = result.data as? [String: Any] else {
                throw NSError(domain: "AppError", code: -1)
            }
            return try self.parseDailyHoroscope(horoscope)
        }

        // Add timeout task
        group.addTask {
            try await Task.sleep(nanoseconds: UInt64(timeout * 1_000_000_000))
            throw TimeoutError()
        }

        // Return first completed task (request or timeout)
        let result = try await group.next()!
        group.cancelAll()
        return result
    }
}

struct TimeoutError: Error {
    var localizedDescription: String {
        "The stars are aligning slowly today. Please try again."
    }
}

// Usage:
Task {
    do {
        let horoscope = try await fetchDailyHoroscope(userId: userId, timeout: 30)
        displayHoroscope(horoscope)
    } catch is TimeoutError {
        showTimeoutError()
    } catch {
        showError(error)
    }
}

func showTimeoutError() {
    errorView.show(
        icon: "🌙",
        title: "The stars are aligning slowly today",
        message: "This is taking longer than usual. Please try again.",
        retryButton: true
    )
}
```

### Performance Notes

- **Network latency**: ~600-700ms base overhead (cold start)
- **LLM generation**: 4-9 seconds (varies by model load)
- **P95 cases**: Can spike to 10-13 seconds
- **Cache strategy**: Same-day horoscopes cached (see Caching Strategy)

### Design for Reality, Not Targets

- ✅ Implement skeleton loaders
- ✅ Show progressive loading messages
- ✅ Set 30-second timeout
- ✅ Cache same-day horoscopes aggressively
- ✅ Load detailed horoscope in background (10+ seconds)
- ❌ Don't show blank screen or simple spinner

**Benchmark script**: Run `python benchmark.py` to measure current performance.

---

## Background Tasks & Notifications

**Feature**: V3+ (Background horoscope precomputation and local notifications)

### Overview

Instead of using remote push notifications (APNS), we recommend using Apple's **BackgroundTasks framework** (`BGAppRefreshTask`) to periodically fetch and cache the daily horoscope in the background. This approach:

- ✅ Works without remote notification infrastructure
- ✅ Runs automatically when device conditions are optimal (charging, Wi-Fi)
- ✅ Reduces backend load (no notification scheduling service needed)
- ✅ Provides better UX (horoscope ready instantly when user opens app)
- ✅ Enables offline access to today's horoscope
- ✅ Uses local notifications (no APNS certificate required)

**⚠️ Cost Consideration:**

Background horoscope generation can be **expensive** since it runs daily for all users regardless of whether they open the app. Each horoscope generation costs ~$0.001-0.005 in LLM costs.

- **100,000 users** × daily generation = ~$100-500/day in LLM costs
- Many users may not open the app daily, resulting in wasted compute

**Recommendation**: Use **Firebase Remote Config** to gate this feature:
- ✅ Enable only for **premium/paying users** initially
- ✅ Monitor costs and user engagement before rolling out to free users
- ✅ A/B test to measure impact on retention vs. cost

See [Feature Gating with Remote Config](#feature-gating-with-remote-config) section below for implementation details.

### How It Works

1. **App schedules a background refresh task** to run after midnight (e.g., 2 AM)
2. **iOS wakes the app in the background** when conditions are optimal
3. **App fetches daily horoscope** from backend (5-10 seconds)
4. **App caches horoscope locally** (UserDefaults or CoreData)
5. **App schedules local notification** with `daily_theme_headline`
6. **App schedules next day's refresh task** (repeat cycle)

### Implementation Steps

#### 1. Enable Background Modes in Xcode

Go to **Signing & Capabilities** → **+ Capability** → **Background Modes**

Check these boxes:
- ✅ **Background Fetch**
- ✅ **Background Processing**

#### 2. Register Task Identifier in Info.plist

Add a new key `BGTaskSchedulerPermittedIdentifiers` (array) and add an item:
```
com.yourapp.fetchHoroscope
```

**Example Info.plist:**
```xml
<key>BGTaskSchedulerPermittedIdentifiers</key>
<array>
    <string>com.yourapp.fetchHoroscope</string>
</array>
```

#### 3. Schedule the Background Task

Call this when the app becomes active (e.g., `applicationDidBecomeActive` or `sceneDidBecomeActive`).

```swift
import BackgroundTasks

func scheduleAppRefresh() {
    let request = BGAppRefreshTaskRequest(identifier: "com.yourapp.fetchHoroscope")

    // Set the earliest time this can run (next day at 2 AM)
    var components = DateComponents()
    components.hour = 2
    components.minute = 0
    let tomorrow = Calendar.current.date(byAdding: .day, value: 1, to: Date())!
    request.earliestBeginDate = Calendar.current.date(bySettingHour: 2, minute: 0, second: 0, of: tomorrow)

    do {
        try BGTaskScheduler.shared.submit(request)
        print("Successfully scheduled daily horoscope refresh for 2 AM.")
    } catch {
        print("Could not schedule app refresh: \(error)")
    }
}
```

**Notes:**
- `earliestBeginDate` is a **hint**, not a guarantee. iOS will run the task when optimal (device charging, Wi-Fi, etc.)
- You can request it to run after midnight, but iOS may run it at 2 AM, 4 AM, or later
- Users with low battery or no Wi-Fi may experience delays
- Always reschedule after each run to maintain daily cycle

#### 4. Handle the Background Task

Register a handler in your `AppDelegate` or `@main App` struct:

```swift
import BackgroundTasks
import Firebase
import UserNotifications

// In AppDelegate.didFinishLaunchingWithOptions or App.init()
func setupBackgroundTasks() {
    BGTaskScheduler.shared.register(
        forTaskWithIdentifier: "com.yourapp.fetchHoroscope",
        using: nil
    ) { task in
        self.handleAppRefresh(task: task as! BGAppRefreshTask)
    }
}

func handleAppRefresh(task: BGAppRefreshTask) {
    // IMPORTANT: Schedule next refresh immediately
    scheduleAppRefresh()

    // Create a background operation
    let operation = BlockOperation {
        await self.fetchAndCacheHoroscope()
    }

    // Set expiration handler (iOS may kill the task if it takes too long)
    task.expirationHandler = {
        operation.cancel()
    }

    // Mark task complete when done
    operation.completionBlock = {
        task.setTaskCompleted(success: !operation.isCancelled)
    }

    // Execute the operation
    let queue = OperationQueue()
    queue.addOperation(operation)
}

func fetchAndCacheHoroscope() async {
    do {
        // 1. Get authenticated user ID
        guard let userId = Auth.auth().currentUser?.uid else {
            print("No authenticated user - skipping background fetch")
            return
        }

        // 2. Fetch today's horoscope from backend
        let today = ISO8601DateFormatter().string(from: Date()).prefix(10)
        let data: [String: Any] = [
            "user_id": userId,
            "date": String(today)
        ]

        let result = try await Functions.functions(region: "us-central1")
            .httpsCallable("get_daily_horoscope")
            .call(data)

        guard let horoscope = result.data as? [String: Any] else {
            print("Invalid horoscope data")
            return
        }

        // 3. Cache horoscope locally
        let cacheKey = "cached_horoscope_\(userId)_\(today)"
        if let jsonData = try? JSONSerialization.data(withJSONObject: horoscope),
           let jsonString = String(data: jsonData, encoding: .utf8) {
            UserDefaults.standard.set(jsonString, forKey: cacheKey)
            UserDefaults.standard.set(String(today), forKey: "cached_horoscope_date")
            print("Horoscope cached for \(today)")
        }

        // 4. Schedule local notification
        let headline = horoscope["daily_theme_headline"] as? String ?? "Your daily horoscope is ready"
        scheduleLocalNotification(title: "✨ Today's Guidance", body: headline)

    } catch {
        print("Background fetch failed: \(error)")
    }
}

func scheduleLocalNotification(title: String, body: String) {
    let content = UNMutableNotificationContent()
    content.title = title
    content.body = body
    content.sound = .default

    // Deliver notification in 1 minute (or immediately)
    let trigger = UNTimeIntervalNotificationTrigger(timeInterval: 60, repeats: false)

    let request = UNNotificationRequest(
        identifier: "daily_horoscope",
        content: content,
        trigger: trigger
    )

    UNUserNotificationCenter.current().add(request) { error in
        if let error = error {
            print("Failed to schedule notification: \(error)")
        } else {
            print("Local notification scheduled")
        }
    }
}
```

#### 5. Request Notification Permissions

Ask for local notification permissions when user first launches the app:

```swift
import UserNotifications

func requestNotificationPermissions() {
    UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, error in
        if granted {
            print("Notification permissions granted")
        } else {
            print("Notification permissions denied")
        }
    }
}
```

### Testing Background Tasks

**IMPORTANT**: Background tasks won't run in the Xcode debugger or simulator during normal operation. You must simulate them manually.

#### Method 1: Using Xcode Console (Recommended)

1. Run your app in the simulator or device
2. Pause the debugger
3. In the LLDB console, run:
   ```
   e -l objc -- (void)[[BGTaskScheduler sharedScheduler] _simulateLaunchForTaskWithIdentifier:@"com.yourapp.fetchHoroscope"]
   ```
4. Resume the debugger
5. Your background task will execute immediately

#### Method 2: Using Scheme Environment Variables

1. Edit your scheme (Product → Scheme → Edit Scheme)
2. Go to **Run** → **Arguments** → **Environment Variables**
3. Add:
   ```
   BGTaskSchedulerSimulatedLaunchIdentifier = com.yourapp.fetchHoroscope
   ```
4. Run the app
5. Background task will execute on next app launch

#### Method 3: Command Line (Device Only)

```bash
# Trigger background task
e -l objc -- (void)[[BGTaskScheduler sharedScheduler] _simulateLaunchForTaskWithIdentifier:@"com.yourapp.fetchHoroscope"]
```

### Production Behavior

In production, the background task will run:
- ✅ After the `earliestBeginDate` you specify (e.g., 2 AM)
- ✅ When device is charging or has sufficient battery
- ✅ When device is on Wi-Fi (cellular ok if Wi-Fi unavailable)
- ✅ When device is idle (not in active use)
- ✅ Based on iOS's heuristics (usage patterns, app importance)

**Caveats:**
- ❌ No guaranteed execution time - iOS decides when to run
- ❌ May not run daily if device conditions aren't met
- ❌ May not run if user rarely uses the app
- ❌ Limited execution time (~30 seconds, sometimes more)

### Fallback Strategy

If background fetch fails (user doesn't grant permissions, iOS doesn't run task, etc.):

```swift
func loadDailyHoroscope() async {
    let today = Calendar.current.startOfDay(for: Date())
    let cacheKey = "cached_horoscope_\(userId)"

    // 1. Check if we have today's horoscope cached
    if let cached = loadCachedHoroscope(),
       Calendar.current.isDate(cached.date, inSameDayAs: today) {
        // Show cached horoscope immediately
        displayHoroscope(cached, isFromCache: true)
        return
    }

    // 2. No cache or cache expired - fetch from backend
    if isOnline {
        do {
            let horoscope = try await fetchHoroscopeFromBackend()
            cacheHoroscope(horoscope)
            displayHoroscope(horoscope, isFromCache: false)
        } catch {
            handleError(error)
        }
    } else {
        showOfflineState()
    }
}
```

### User Settings (Optional)

Allow users to customize notification timing and preferences:

```swift
struct NotificationSettings {
    var enabled: Bool = true
    var preferredTime: DateComponents = DateComponents(hour: 9, minute: 0)  // 9 AM default
}

func scheduleAppRefreshWithUserPreferences(settings: NotificationSettings) {
    guard settings.enabled else { return }

    let request = BGAppRefreshTaskRequest(identifier: "com.yourapp.fetchHoroscope")

    // Use user's preferred time
    let tomorrow = Calendar.current.date(byAdding: .day, value: 1, to: Date())!
    let preferredTime = Calendar.current.date(
        bySettingHour: settings.preferredTime.hour ?? 9,
        minute: settings.preferredTime.minute ?? 0,
        second: 0,
        of: tomorrow
    )

    request.earliestBeginDate = preferredTime

    do {
        try BGTaskScheduler.shared.submit(request)
    } catch {
        print("Failed to schedule: \(error)")
    }
}
```

### Analytics & Debugging

Track background fetch success/failure for debugging:

```swift
func handleAppRefresh(task: BGAppRefreshTask) {
    let startTime = Date()

    scheduleAppRefresh()

    let operation = BlockOperation {
        await self.fetchAndCacheHoroscope()
    }

    task.expirationHandler = {
        operation.cancel()

        // Log timeout
        print("Background fetch timed out")
        // Optional: Track in analytics
    }

    operation.completionBlock = {
        let duration = Date().timeIntervalSince(startTime)
        let success = !operation.isCancelled

        print("Background fetch \(success ? "succeeded" : "failed") in \(duration)s")
        // Optional: Track in analytics

        task.setTaskCompleted(success: success)
    }

    let queue = OperationQueue()
    queue.addOperation(operation)
}
```

### Best Practices

1. **Always reschedule** - Call `scheduleAppRefresh()` at the start of your handler, not the end
2. **Handle expiration** - Set `task.expirationHandler` to cancel long-running work
3. **Mark completion** - Always call `task.setTaskCompleted(success:)` when done
4. **Graceful fallback** - Check cache first, fetch on-demand if background fetch failed
5. **Test thoroughly** - Use Xcode console to simulate background launches
6. **Track success rate** - Log background fetch success/failure for debugging
7. **Respect user battery** - Don't schedule multiple tasks or use excessive resources

### Alternative: Silent Push Notifications

If you need guaranteed delivery and precise timing, consider **silent push notifications** (APNS):

**Pros:**
- ✅ Guaranteed delivery (as long as user is online)
- ✅ Precise timing control (backend triggers at specific time)
- ✅ Works even if user hasn't opened the app recently

**Cons:**
- ❌ Requires APNS certificate setup
- ❌ Requires backend notification scheduling service
- ❌ Requires device to be online
- ❌ User must grant notification permissions
- ❌ May be throttled by iOS if overused

**When to use:**
- If you need guaranteed daily delivery
- If timing precision is critical (e.g., exactly at 9 AM)
- If you have existing APNS infrastructure

**Implementation** (not recommended for V3 - use BackgroundTasks instead):
```swift
// Register for remote notifications
UIApplication.shared.registerForRemoteNotifications()

// Handle silent push in AppDelegate
func application(_ application: UIApplication, didReceiveRemoteNotification userInfo: [AnyHashable: Any], fetchCompletionHandler completionHandler: @escaping (UIBackgroundFetchResult) -> Void) {
    // Fetch horoscope and cache
    Task {
        await fetchAndCacheHoroscope()
        completionHandler(.newData)
    }
}
```

### Recommendation

**For V3, use BackgroundTasks framework (`BGAppRefreshTask`)** - it's simpler, doesn't require server infrastructure, and provides a better UX with precomputed horoscopes. Users get instant loading when they open the app.

---

## Need Help?

- **Backend Issues**: Check Firebase Functions logs in Firebase Console
- **Data Issues**: Check Firestore data in Firebase Console
- **Integration Issues**: Run `integration_test.py` to verify backend
- **Production Test**: Run `prod_test.py` to test deployed functions

---

## Changelog

**2025-10-20b**: Added Background Tasks & Notifications section
- ✅ Complete implementation guide for V3 background horoscope precomputation
- ✅ BackgroundTasks framework (`BGAppRefreshTask`) recommended approach
- ✅ Local notifications using `daily_theme_headline` field
- ✅ Testing instructions and production behavior notes
- ✅ Fallback strategy for when background fetch fails
- ✅ Optional user settings for notification timing
- ✅ Analytics and debugging best practices
- ✅ Comparison with silent push notifications (APNS)

**2025-10-20**: Updated Swift syntax to async/await, clarified feature roadmap
- ✅ All code examples modernized to use async/await (no completion handlers)
- ✅ Added structured types (DailyHoroscope, DetailedHoroscope, etc.)
- ✅ Clarified push notifications are V3 feature
- ✅ Clarified premium subscriptions are post-V4 feature
- ✅ Noted `is_premium`/`premium_expiry` fields prepared for future use

**2025-10-19**: Initial version - All 6 core functions deployed and tested
- ✅ Onboarding flow (sun sign + profile creation)
- ✅ Two-prompt horoscope generation
- ✅ Journal entry + memory trigger
- ✅ Secrets configured (GEMINI_API_KEY, POSTHOG_API_KEY)
