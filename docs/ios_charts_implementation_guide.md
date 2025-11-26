# iOS Implementation Guide: Charts & Compatibility

**Version:** 1.0
**Date:** 2025-11-25
**For:** iOS Development Team

---

## Mental Model

### The "Your World" Architecture

Each user maintains their own private "world" of connections. When you add someone via their share link, you get a **copy** of their birth data in your world. They don't see your connections, you don't see theirs.

```
User A's World                    User B's World
├── My Profile                    ├── My Profile
├── Connections/                  ├── Connections/
│   ├── Sarah (friend)           │   ├── User A (romantic)
│   ├── John (coworker)          │   └── Mike (family)
│   └── User B (romantic)        │
```

**Two ways to add connections:**

1. **Manual entry (private)**: User enters someone's birth data directly. Completely private - the person doesn't need to be an Arca user and is never notified.

2. **Via share link (social)**: User imports someone via their Arca share link. The profile owner gets notified and can add back.

**Key insight:** When User A imports User B via share link, User B gets notified but doesn't automatically have User A in their connections. They must add User A back (via notification or User A's share link).

### iOS Owns All Caching

Backend computes everything fresh. iOS is responsible for:
- Caching natal chart data (permanent - doesn't change)
- Caching compatibility results (per connection, invalidate on birth data change)
- Caching transit chart data (daily - refresh each day)

### Categories by Relationship Mode

Each mode returns **different categories** based on what matters for that relationship type:

**Romantic Mode (6 categories):**
| ID | Name | What it measures |
|----|------|------------------|
| `emotional` | Emotional Connection | How you feel together, emotional safety |
| `communication` | Communication | How you talk, understand each other |
| `attraction` | Attraction | Physical/romantic chemistry |
| `values` | Shared Values | What you both want in life |
| `longTerm` | Long-term Potential | Staying power, commitment compatibility |
| `growth` | Growth Together | How you challenge and evolve each other |

**Friendship Mode (5 categories):**
| ID | Name | What it measures |
|----|------|------------------|
| `emotional` | Emotional Bond | Emotional understanding, empathy |
| `communication` | Communication | Conversation flow, humor |
| `fun` | Fun & Adventure | How much fun you have together |
| `loyalty` | Loyalty & Support | Reliability, being there for each other |
| `sharedInterests` | Shared Interests | Common ground, activities |

**Coworker Mode (5 categories):**
| ID | Name | What it measures |
|----|------|------------------|
| `communication` | Communication | Professional communication style |
| `collaboration` | Collaboration | How well you work together |
| `reliability` | Reliability | Dependability, follow-through |
| `ambition` | Ambition Alignment | Shared goals, drive compatibility |
| `powerDynamics` | Power Dynamics | Leadership balance, conflict potential |

**UI Note:** Design your category display to handle different numbers of categories per mode. Don't hardcode 6 categories.

---

### Relationship Weather in Daily Horoscope

The daily horoscope includes relationship-specific content:

**`relationship_weather` structure:**
```swift
struct RelationshipWeather: Codable {
    let overview: String                     // General paragraph for all relationship types
    let connectionVibes: [ConnectionVibe]    // Top 10 connections with today's vibe
}

struct ConnectionVibe: Codable, Identifiable {
    let connectionId: String                 // Use this to link to compatibility view
    let name: String
    let relationshipType: RelationshipType
    let vibe: String                         // "Good day to collaborate with John - ideas will click."
    let vibeScore: Int                       // 0-100, for visual indicator
    let keyTransit: String                   // Technical explanation for "why?" tap

    var id: String { connectionId }
}

// Example vibe strings (personalized with name):
// "Today's a great day to connect with Sarah - harmony flows easily between you two."
// "Good day to collaborate with John - ideas will click."
// "Give Mike some space today - tension is in the air."
// "Perfect time to have that heart-to-heart with Emma."
```

**iOS Display:**
1. Show `overview` in Today tab under "Relationships" section
2. Show `connectionVibes` as a horizontal scroll of cards or list
3. Tapping a connection vibe → Navigate to full compatibility view
4. "Why?" tap → Show `keyTransit` explanation

**Note:** `connectionVibes` may be empty if user has no connections yet.

---

### Where LLM Calls Happen

**Fast endpoints (no LLM):**
- `create_connection` - Just saves birth data
- `list_connections` - Just reads from Firestore
- `delete_connection` - Just deletes
- `import_connection` - Just copies data

**Slow endpoints (LLM generates interpretations):**
- `get_natal_chart` - LLM writes planet/aspect interpretations (2-5 seconds)
- `get_transit_chart` - LLM writes transit interpretations (2-5 seconds)
- `get_compatibility` - LLM writes all category summaries, aspect interpretations, relationship verb, composite summary (3-8 seconds)

**Key UX implication:**
- Creating a connection is instant
- VIEWING the compatibility (first time) requires a loading screen
- Subsequent views are instant (cached)

---

## Data Models to Create

### Connection.swift

```swift
struct Connection: Codable, Identifiable {
    let connectionId: String
    let name: String
    let birthDate: String                    // "YYYY-MM-DD"
    let birthTime: String?                   // "HH:MM" or nil
    let birthLat: Double?
    let birthLon: Double?
    let birthTimezone: String?
    let relationshipType: RelationshipType
    let sourceUserId: String?                // Who they imported from
    let createdAt: Date

    var id: String { connectionId }

    var hasExactBirthTime: Bool { birthTime != nil }
    var hasLocation: Bool { birthLat != nil && birthLon != nil }
}

enum RelationshipType: String, Codable, CaseIterable {
    case friend
    case romantic
    case family
    case coworker

    var displayName: String {
        switch self {
        case .friend: return "Friend"
        case .romantic: return "Romantic"
        case .family: return "Family"
        case .coworker: return "Coworker"
        }
    }

    var icon: String {
        switch self {
        case .friend: return "person.2"
        case .romantic: return "heart"
        case .family: return "house"
        case .coworker: return "briefcase"
        }
    }
}
```

### ChartGeometry.swift

```swift
struct ChartGeometry: Codable {
    let planets: [PlanetGeometry]
    let houses: [HouseGeometry]
    let aspects: [AspectGeometry]
    let angles: AngleGeometry
}

struct PlanetGeometry: Codable, Identifiable {
    let name: String
    let sign: String
    let signSymbol: String
    let degree: Double
    let signedDegree: Double
    let house: Int
    let retrograde: Bool
    let element: String
    let modality: String
    let dms: String
    let displayX: Double                     // 0.0-1.0 normalized
    let displayY: Double                     // 0.0-1.0 normalized
    let interpretation: String

    var id: String { name }

    // Convert to screen coordinates
    func screenPosition(in size: CGSize) -> CGPoint {
        CGPoint(
            x: displayX * size.width,
            y: displayY * size.height
        )
    }
}

struct AspectGeometry: Codable, Identifiable {
    let body1: String
    let body2: String
    let aspectType: String
    let aspectSymbol: String
    let orb: Double
    let applying: Bool
    let x1: Double
    let y1: Double
    let x2: Double
    let y2: Double
    let interpretation: String

    var id: String { "\(body1)_\(aspectType)_\(body2)" }

    var isHarmonious: Bool {
        ["trine", "sextile", "conjunction"].contains(aspectType)
    }

    func linePoints(in size: CGSize) -> (start: CGPoint, end: CGPoint) {
        (
            CGPoint(x: x1 * size.width, y: y1 * size.height),
            CGPoint(x: x2 * size.width, y: y2 * size.height)
        )
    }
}
```

### CompatibilityResult.swift

```swift
struct CompatibilityResult: Codable {
    let romantic: ModeResult
    let friendship: ModeResult
    let coworker: ModeResult
    let aspects: [SynastryAspect]
    let compositeSummary: CompositeSummary
    let calculatedAt: Date
}

struct ModeResult: Codable {
    let overallScore: Int                    // 0-100
    let relationshipVerb: String             // "You spark each other"
    let categories: [CategoryScore]          // Different categories per mode!
    let missingDataPrompts: [String]
}

// NOTE: Each mode returns DIFFERENT categories
// Romantic:  emotional, communication, attraction, values, longTerm, growth
// Friendship: emotional, communication, fun, loyalty, sharedInterests
// Coworker:  communication, collaboration, reliability, ambition, powerDynamics

struct CategoryScore: Codable, Identifiable {
    let id: String                           // "emotional", "communication", etc.
    let name: String
    let score: Int                           // -100 to +100
    let summary: String
    let aspectIds: [String]

    var isPositive: Bool { score >= 0 }

    var compatibilityLabel: String {
        switch score {
        case 50...: return "Strong Match"
        case 20..<50: return "Good Match"
        case -20..<20: return "Neutral"
        case -50..<(-20): return "Needs Work"
        default: return "Challenging"
        }
    }
}

struct SynastryAspect: Codable, Identifiable {
    let id: String
    let userPlanet: String
    let theirPlanet: String
    let aspectType: String
    let orb: Double
    let interpretation: String
    let isHarmonious: Bool
}

struct CompositeSummary: Codable {
    let compositeSun: String
    let compositeMoon: String?               // nil if birth time missing
    let summary: String
    let strengths: [String]
    let challenges: [String]
}
```

### ShareProfile.swift

```swift
struct ShareProfile: Codable {
    let name: String
    let birthDate: String
    let birthTime: String?
    let birthLat: Double?
    let birthLon: Double?
    let birthTimezone: String?
    let sunSign: String
}

struct PublicProfileResponse: Codable {
    let profile: ShareProfile
    let shareMode: ShareMode
    let canAdd: Bool
    let message: String?                     // For request mode
}

enum ShareMode: String, Codable {
    case `public`
    case request
}
```

---

## Caching Strategy

### What to Cache

| Data | Cache Duration | Invalidation |
|------|----------------|--------------|
| User's natal chart | Forever | Never (birth data doesn't change) |
| Connection's natal chart | Forever | On connection birth data update |
| Transit chart | 24 hours | Daily refresh |
| Compatibility result | 7 days | On connection birth data update |
| Connections list | Real-time | Firestore listener |

### Cache Implementation

```swift
class ChartCache {
    private let userDefaults = UserDefaults.standard

    // Natal chart - cache forever
    func cacheNatalChart(_ chart: ChartGeometry, for userId: String) {
        let key = "natal_chart_\(userId)"
        if let data = try? JSONEncoder().encode(chart) {
            userDefaults.set(data, forKey: key)
        }
    }

    func getNatalChart(for userId: String) -> ChartGeometry? {
        let key = "natal_chart_\(userId)"
        guard let data = userDefaults.data(forKey: key) else { return nil }
        return try? JSONDecoder().decode(ChartGeometry.self, from: data)
    }

    // Transit chart - cache with date validation
    func cacheTransitChart(_ chart: ChartGeometry, date: Date) {
        let key = "transit_\(dateKey(date))"
        if let data = try? JSONEncoder().encode(chart) {
            userDefaults.set(data, forKey: key)
        }
    }

    func getTransitChart(for date: Date) -> ChartGeometry? {
        let key = "transit_\(dateKey(date))"
        guard let data = userDefaults.data(forKey: key) else { return nil }
        return try? JSONDecoder().decode(ChartGeometry.self, from: data)
    }

    // Compatibility - cache with connection ID
    func cacheCompatibility(_ result: CompatibilityResult, connectionId: String) {
        let key = "compat_\(connectionId)"
        if let data = try? JSONEncoder().encode(result) {
            userDefaults.set(data, forKey: key)
            userDefaults.set(Date(), forKey: "\(key)_date")
        }
    }

    func getCompatibility(connectionId: String) -> CompatibilityResult? {
        let key = "compat_\(connectionId)"
        guard let data = userDefaults.data(forKey: key),
              let cachedDate = userDefaults.object(forKey: "\(key)_date") as? Date,
              Date().timeIntervalSince(cachedDate) < 7 * 24 * 60 * 60 // 7 days
        else { return nil }
        return try? JSONDecoder().decode(CompatibilityResult.self, from: data)
    }

    func invalidateCompatibility(connectionId: String) {
        let key = "compat_\(connectionId)"
        userDefaults.removeObject(forKey: key)
        userDefaults.removeObject(forKey: "\(key)_date")
    }

    private func dateKey(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: date)
    }
}
```

---

## User Flows

### Flow 1: View My Natal Chart

```
1. Check cache for natal chart
2. If cached -> Display immediately (instant)
3. If not cached (first time):
   a. Show loading screen
      - "Mapping your stars..."
      - Takes 2-5 seconds (LLM generating interpretations)
   b. Call get_natal_chart
   c. Cache response permanently (birth chart never changes)
   d. Display chart
4. User taps planet -> Show interpretation (already in cached response)
5. User taps aspect line -> Show aspect meaning (already in cached response)
```

### Flow 2: Add Connection Manually (Private)

User adds someone to their own world by entering birth data directly. No sharing involved.

```
1. User taps "Add Connection" in Connections tab
2. User enters:
   - Name (required)
   - Birth date (required)
   - Birth time (optional)
   - Birth location (optional)
   - Relationship type (friend/romantic/family/coworker)
3. Call create_connection
4. Connection added to user's private list
5. Navigate to compatibility view
```

**Note:** This is completely private. The person being added is NOT notified and doesn't need to be an Arca user.

### Flow 3: Add Connection via Share Link

When someone shares their Arca profile link with user.

```
1. User taps share link (arca-app.com/u/abc123)
2. App opens via Universal Link
3. Extract share_secret from URL
4. Call get_public_profile(share_secret)
5. If share_mode == "public":
   a. Show profile preview (name, sun sign)
   b. User selects relationship type
   c. Call import_connection
   d. Add to local connections list
   e. Navigate to compatibility view
6. If share_mode == "request":
   a. Show "John requires approval" message
   b. User can send request
   c. Show pending state
```

### Flow 4: View Compatibility

```
1. User selects connection from list
2. Check cache for compatibility result
3. If cached and valid -> Display immediately (instant)
4. If not cached (first time viewing this connection):
   a. Show loading screen with progress indicator
      - "Analyzing your cosmic connection..."
      - This takes 3-8 seconds (LLM generating interpretations)
   b. Call get_compatibility(connection_id)
   c. Cache full response
   d. Display result
5. User can switch modes (romantic/friendship/coworker) instantly
   (all 3 modes returned in single response - no additional API call)
6. Tapping "Why?" on a category -> show related aspects (already in response)
```

**Loading state matters:** The first compatibility view is the "reveal moment" - consider a nice animation or progress steps.

### Flow 5: Share My Profile

```
1. User taps "Share My Arca" button
2. Call get_share_link
3. Display share options:
   - Copy link
   - Share sheet (Messages, etc.)
   - QR code
4. Settings: Toggle public/request mode
```

### Flow 6: Handle Incoming Notification

```
1. Receive push: "Sarah added you! Add her back to see compatibility"
2. User taps notification
3. Deep link to Sarah's profile (via share_secret in notification payload)
4. Show Sarah's public profile
5. User can add Sarah with one tap
```

---

## Deep Linking

### Universal Link Configuration

```
Domain: arca-app.com
Paths:
  /u/{share_secret}  ->  Profile import
```

### AppDelegate/SceneDelegate

```swift
func scene(_ scene: UIScene, continue userActivity: NSUserActivity) {
    guard let url = userActivity.webpageURL else { return }
    handleDeepLink(url)
}

func handleDeepLink(_ url: URL) {
    // Parse: https://arca-app.com/u/abc123xyz
    guard url.host == "arca-app.com",
          url.pathComponents.count >= 2,
          url.pathComponents[1] == "u"
    else { return }

    let shareSecret = url.pathComponents[2]
    navigateToProfileImport(shareSecret: shareSecret)
}
```

---

## UI State Management

### ConnectionsManager

```swift
@MainActor
class ConnectionsManager: ObservableObject {
    @Published var connections: [Connection] = []
    @Published var pendingRequests: [ConnectionRequest] = []
    @Published var isLoading = false
    @Published var error: Error?

    private let cache = ChartCache()
    private var firestoreListener: ListenerRegistration?

    init() {
        setupFirestoreListener()
    }

    private func setupFirestoreListener() {
        // Listen to connections/ subcollection for real-time updates
        let userId = Auth.auth().currentUser?.uid ?? ""
        firestoreListener = Firestore.firestore()
            .collection("users").document(userId)
            .collection("connections")
            .addSnapshotListener { [weak self] snapshot, error in
                guard let documents = snapshot?.documents else { return }
                self?.connections = documents.compactMap { doc in
                    try? doc.data(as: Connection.self)
                }
            }
    }

    func addConnection(shareSecret: String, relationshipType: RelationshipType) async throws {
        isLoading = true
        defer { isLoading = false }

        let result = try await Functions.functions()
            .httpsCallable("import_connection")
            .call([
                "share_secret": shareSecret,
                "relationship_type": relationshipType.rawValue
            ])

        // Connection will appear via Firestore listener
    }

    func getCompatibility(for connection: Connection) async throws -> CompatibilityResult {
        // Check cache first
        if let cached = cache.getCompatibility(connectionId: connection.connectionId) {
            return cached
        }

        let result = try await Functions.functions()
            .httpsCallable("get_compatibility")
            .call(["connection_id": connection.connectionId])

        let compatibility = try JSONDecoder().decode(
            CompatibilityResult.self,
            from: JSONSerialization.data(withJSONObject: result.data)
        )

        cache.cacheCompatibility(compatibility, connectionId: connection.connectionId)
        return compatibility
    }
}
```

### CompatibilityViewModel

```swift
@MainActor
class CompatibilityViewModel: ObservableObject {
    @Published var result: CompatibilityResult?
    @Published var selectedMode: RelationshipType = .romantic
    @Published var isLoading = false
    @Published var error: Error?

    let connection: Connection

    var currentModeResult: ModeResult? {
        switch selectedMode {
        case .romantic: return result?.romantic
        case .friend: return result?.friendship
        case .coworker: return result?.coworker
        case .family: return result?.friendship // Use friendship for family
        }
    }

    init(connection: Connection) {
        self.connection = connection
    }

    func loadCompatibility() async {
        isLoading = true
        defer { isLoading = false }

        do {
            result = try await ConnectionsManager.shared.getCompatibility(for: connection)
        } catch {
            self.error = error
        }
    }

    // Mode switching is instant - no API call needed
    func selectMode(_ mode: RelationshipType) {
        selectedMode = mode
    }
}
```

---

## Error Handling

### Error Types

```swift
enum ChartError: LocalizedError {
    case missingBirthData
    case rateLimitExceeded(retryAfter: Int)
    case networkError
    case serverError(String)

    var errorDescription: String? {
        switch self {
        case .missingBirthData:
            return "Birth data is incomplete"
        case .rateLimitExceeded(let seconds):
            return "Too many requests. Try again in \(seconds / 60) minutes."
        case .networkError:
            return "Check your internet connection"
        case .serverError(let message):
            return message
        }
    }
}
```

### Missing Data UI

When `missingDataPrompts` is not empty, show prompts to user:

```swift
struct MissingDataView: View {
    let prompts: [String]
    let connection: Connection

    var body: some View {
        VStack(spacing: 12) {
            ForEach(prompts, id: \.self) { prompt in
                HStack {
                    Image(systemName: "info.circle")
                        .foregroundColor(.orange)
                    Text(prompt)
                        .font(.subheadline)
                }
            }

            Button("Update Birth Info") {
                // Navigate to edit connection
            }
        }
        .padding()
        .background(Color.orange.opacity(0.1))
        .cornerRadius(12)
    }
}
```

---

## Notifications

### Register for Push

Backend sends push notification when someone adds user via share link.

**Notification Payload:**
```json
{
  "aps": {
    "alert": {
      "title": "New Connection",
      "body": "Sarah added you! Add her back to see compatibility"
    }
  },
  "share_secret": "abc123xyz",
  "action": "profile_import"
}
```

### Handle Notification

```swift
func userNotificationCenter(
    _ center: UNUserNotificationCenter,
    didReceive response: UNNotificationResponse
) async {
    let userInfo = response.notification.request.content.userInfo

    if let action = userInfo["action"] as? String,
       action == "profile_import",
       let shareSecret = userInfo["share_secret"] as? String {
        // Navigate to profile import flow
        await MainActor.run {
            navigateToProfileImport(shareSecret: shareSecret)
        }
    }
}
```

---

## Testing Checklist

- [ ] Cache natal chart on first load
- [ ] Cache compatibility result per connection
- [ ] Invalidate cache when connection birth data changes
- [ ] Mode switching works instantly (no loading)
- [ ] Deep link handling for share URLs
- [ ] Push notification opens correct flow
- [ ] Rate limit error shows appropriate message
- [ ] Missing data prompts display correctly
- [ ] Share sheet works (link + QR code)
- [ ] Public vs Request mode shows different UI
- [ ] Firestore listener updates connections in real-time

---

## Timeline Recommendation

### Phase 1: Data Layer (Week 1)
- Create Swift models
- Implement cache manager
- Set up Firestore listeners for connections

### Phase 2: Charts Tab (Week 2)
- Natal chart visualization component
- Transit chart with overlay toggle
- Integration with `get_natal_chart` and `get_transit_chart`

### Phase 3: Connections Tab (Week 3)
- Connections list view
- Add connection flow (manual + share link)
- Share link generation + QR code

### Phase 4: Compatibility (Week 4)
- Compatibility result display
- Mode switching UI
- Category detail views
- "Why?" drill-down to aspects

### Phase 5: Polish (Week 5)
- Deep linking
- Push notifications
- Error handling
- Missing data prompts
- Settings (public/request mode)
