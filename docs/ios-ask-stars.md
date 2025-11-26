# Ask the Stars - iOS Integration Guide

**Ask the Stars** is a conversational Q&A feature that lets users ask personalized questions about their day, relationships, career, and life situations through the lens of their daily horoscope and astrological transits.

## Overview

Users can have real-time conversations with an AI astrologer that understands:
- Their birth chart and sun sign
- Today's transits and astrological influences
- Their daily horoscope and meter readings
- Context from previous conversations (entities)
- Their personal memory and patterns

## Feature Flow

```
1. User opens Daily Horoscope
   ↓
2. Sees "follow_up_questions" (3-5 suggested questions)
   ↓
3. Taps a question OR types their own
   ↓
4. Backend extracts entities → streams response via SSE
   ↓
5. User sees typing animation → full answer appears
   ↓
6. Can continue conversation (multi-turn)
```

## New Field in Daily Horoscope Response

The `DailyHoroscope` model now includes:

```json
{
  "date": "2025-01-24",
  "sun_sign": "gemini",
  "daily_theme_headline": "...",
  "daily_overview": "...",
  "actionable_advice": { ... },
  "astrometers": { ... },
  "follow_up_questions": [
    "How can I make the most of today's creative energy?",
    "What should I watch out for in my relationships today?",
    "How can I navigate the tension I'm feeling at work?"
  ],
  ...
}
```

### `follow_up_questions` (Array of Strings)

**Purpose:** Provide 3-5 contextual conversation starters based on today's horoscope.

**Characteristics:**
- **Personalized** - Based on user's sun sign, astrometers, and transit themes
- **Actionable** - Framed as questions the user would naturally ask
- **Diverse** - Cover different life areas (relationships, career, emotions, growth)
- **Natural** - Written in conversational tone (not formal astrology jargon)

**Example questions:**
```
"How can I use today's intuitive energy for my creative projects?"
"What's the best way to handle the tension I'm feeling in my relationship?"
"Should I speak up about what's bothering me at work today?"
"How can I balance my need for rest with my responsibilities?"
"What's trying to shift in my life right now?"
```

## iOS UI Recommendations

### 1. Daily Horoscope Screen - Question Prompts

Display `follow_up_questions` as interactive chips/buttons below the horoscope content:

### 2. Ask the Stars Screen - Conversation View

Standard chat interface with:
- User messages (right-aligned)
- AI responses (left-aligned with typing animation)
- Input field at bottom
- Suggested follow-ups can appear after each AI response

## Backend Integration

### Endpoint: `ask_the_stars` (SSE Streaming)

**URL:** `https://us-central1-{project-id}.cloudfunctions.net/ask_the_stars`

**Method:** `POST`

**Headers:**
```
Authorization: Bearer {firebase_id_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "question": "How can I make the most of today's creative energy?",
  "horoscope_date": "2025-01-24",
  "conversation_id": "conv_abc123"  // Optional (omit for new conversation)
}
```

**Response:** Server-Sent Events (SSE) stream

```
data: {"type": "chunk", "text": "Hey Elie, "}

data: {"type": "chunk", "text": "I see you're "}

data: {"type": "chunk", "text": "asking about creativity today. "}

...

data: {"type": "done", "conversation_id": "conv_abc123", "message_id": "msg_def456"}
```

## iOS Implementation (Swift)

### 1. Parse `follow_up_questions` from Daily Horoscope

```swift
struct DailyHoroscope: Codable {
    let date: String
    let sunSign: String
    let dailyThemeHeadline: String
    let dailyOverview: String
    let actionableAdvice: ActionableAdvice
    let astrometers: AstrometersForIOS
    let followUpQuestions: [String]  // NEW FIELD
    // ... other fields
}
```

### 2. Display Follow-Up Questions as Buttons

```swift
struct FollowUpQuestionsView: View {
    let questions: [String]
    let onQuestionTapped: (String) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Ask the Stars 🌟")
                .font(.headline)

            ForEach(questions, id: \.self) { question in
                Button(action: { onQuestionTapped(question) }) {
                    Text(question)
                        .font(.body)
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.blue.opacity(0.1))
                        .cornerRadius(12)
                }
            }
        }
        .padding()
    }
}
```

### 3. SSE Streaming Client

```swift
import Foundation

class AskTheStarsService {
    func streamAnswer(
        question: String,
        horoscopeDate: String,
        conversationId: String?,
        onChunk: @escaping (String) -> Void,
        onComplete: @escaping (String, String) -> Void,
        onError: @escaping (Error) -> Void
    ) {
        guard let url = URL(string: "https://us-central1-arca-backend.cloudfunctions.net/ask_the_stars") else {
            onError(NSError(domain: "Invalid URL", code: -1))
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        // Get Firebase ID token
        Auth.auth().currentUser?.getIDToken { token, error in
            guard let token = token else {
                onError(error ?? NSError(domain: "Auth failed", code: -1))
                return
            }

            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

            // Build request body
            var body: [String: Any] = [
                "question": question,
                "horoscope_date": horoscopeDate
            ]
            if let conversationId = conversationId {
                body["conversation_id"] = conversationId
            }

            request.httpBody = try? JSONSerialization.data(withJSONObject: body)

            // Start SSE stream
            let task = URLSession.shared.dataTask(with: request) { data, response, error in
                if let error = error {
                    onError(error)
                    return
                }

                guard let data = data else {
                    onError(NSError(domain: "No data", code: -1))
                    return
                }

                // Parse SSE stream
                let text = String(data: data, encoding: .utf8) ?? ""
                let lines = text.components(separatedBy: "\n")

                for line in lines {
                    if line.hasPrefix("data: ") {
                        let jsonString = String(line.dropFirst(6))

                        if let jsonData = jsonString.data(using: .utf8),
                           let event = try? JSONDecoder().decode(SSEEvent.self, from: jsonData) {

                            switch event.type {
                            case "chunk":
                                onChunk(event.text ?? "")
                            case "done":
                                onComplete(event.conversationId ?? "", event.messageId ?? "")
                            default:
                                break
                            }
                        }
                    }
                }
            }

            task.resume()
        }
    }
}

struct SSEEvent: Codable {
    let type: String
    let text: String?
    let conversationId: String?
    let messageId: String?

    enum CodingKeys: String, CodingKey {
        case type
        case text
        case conversationId = "conversation_id"
        case messageId = "message_id"
    }
}
```

### 4. Conversation View with Typing Animation

```swift
struct ConversationView: View {
    @State private var messages: [ChatMessage] = []
    @State private var inputText: String = ""
    @State private var isTyping: Bool = false
    @State private var currentConversationId: String?

    let horoscopeDate: String
    let service = AskTheStarsService()

    var body: some View {
        VStack {
            ScrollView {
                ForEach(messages) { message in
                    MessageBubble(message: message)
                }

                if isTyping {
                    TypingIndicator()
                }
            }

            HStack {
                TextField("Ask a question...", text: $inputText)
                    .textFieldStyle(RoundedBorderTextFieldStyle())

                Button(action: sendMessage) {
                    Image(systemName: "paperplane.fill")
                }
                .disabled(inputText.isEmpty)
            }
            .padding()
        }
        .navigationTitle("Ask the Stars")
    }

    func sendMessage() {
        let question = inputText
        inputText = ""

        // Add user message
        messages.append(ChatMessage(role: .user, content: question))

        // Show typing indicator
        isTyping = true
        var accumulatedText = ""

        service.streamAnswer(
            question: question,
            horoscopeDate: horoscopeDate,
            conversationId: currentConversationId,
            onChunk: { chunk in
                DispatchQueue.main.async {
                    accumulatedText += chunk

                    // Update last message or create new one
                    if let lastIndex = messages.lastIndex(where: { $0.role == .assistant && $0.isStreaming }) {
                        messages[lastIndex].content = accumulatedText
                    } else {
                        messages.append(ChatMessage(role: .assistant, content: accumulatedText, isStreaming: true))
                    }
                }
            },
            onComplete: { conversationId, messageId in
                DispatchQueue.main.async {
                    isTyping = false
                    currentConversationId = conversationId

                    // Mark message as complete
                    if let lastIndex = messages.lastIndex(where: { $0.role == .assistant }) {
                        messages[lastIndex].isStreaming = false
                    }
                }
            },
            onError: { error in
                DispatchQueue.main.async {
                    isTyping = false
                    print("Error: \(error)")
                }
            }
        )
    }
}

struct ChatMessage: Identifiable {
    let id = UUID()
    let role: MessageRole
    var content: String
    var isStreaming: Bool = false
}

enum MessageRole {
    case user
    case assistant
}
```

## Entity Tracking (Automatic)

The backend automatically:
1. **Extracts entities** from each user message (people, places, companies, events)
2. **Merges entities** with existing tracked entities (deduplication)
3. **Uses entities** in future conversations for personalization

**Example:**
```
User: "I'm nervous about my interview at Google tomorrow"
→ Backend extracts: "Google" (company), "interview" (event)
→ Next question: "How did the interview go?"
→ AI knows about Google interview from context
```

You don't need to do anything - entity tracking happens automatically in the background.

## Conversation Persistence

- Each conversation has a unique `conversation_id`
- Messages are stored in Firestore: `conversations/{conversation_id}`
- **First message:** Omit `conversation_id` → backend creates new conversation
- **Follow-up messages:** Include `conversation_id` → backend appends to existing conversation

**Storage:**
```
Firestore:
  conversations/
    conv_abc123/
      conversation_id: "conv_abc123"
      user_id: "user_xyz"
      horoscope_date: "2025-01-24"
      messages: [
        { role: "user", content: "...", timestamp: "..." },
        { role: "assistant", content: "...", timestamp: "..." }
      ]
      created_at: "..."
      updated_at: "..."
```

## Error Handling

### Common Errors

1. **Missing horoscope:**
```json
{
  "error": "Horoscope for 2025-01-24 not found"
}
```
**Solution:** User must fetch daily horoscope first

2. **Authentication failed:**
```json
{
  "error": "Authentication failed: ..."
}
```
**Solution:** Refresh Firebase ID token

3. **Missing question:**
```json
{
  "error": "Missing question or horoscope_date"
}
```
**Solution:** Ensure both fields are in request body

## Best Practices

### 1. Pre-fetch Daily Horoscope
- Always fetch daily horoscope before showing Ask the Stars
- Display `follow_up_questions` on the horoscope screen
- Don't allow Ask the Stars if horoscope is missing

### 2. Handle Streaming Gracefully
- Show typing indicator while streaming
- Append chunks to message in real-time
- Handle network interruptions (retry logic)

### 3. Conversation Management
- Store `conversation_id` locally for multi-turn conversations
- Clear conversation when user starts new day
- Limit conversation history to 10 messages (backend does this automatically)

### 4. User Experience
- **Typing animation** - Show dots while waiting for first chunk
- **Smooth scrolling** - Auto-scroll to bottom as chunks arrive
- **Copy/Share** - Allow users to copy AI responses
- **Suggested questions** - Show follow-ups after each response

### 5. Rate Limiting
- Prevent spam by debouncing input (500ms)
- Disable send button while streaming
- Show loading state clearly

## Example User Journey

```
1. User opens Daily Horoscope (9:00 AM)
   → Sees: "Today's a great day for creative projects"
   → Sees follow-up questions:
     - "How can I make the most of today's creative energy?"
     - "What should I watch out for in relationships?"

2. User taps: "How can I make the most of today's creative energy?"
   → Backend receives question
   → Extracts entities: "creative" (theme)
   → Streams response using horoscope context

3. AI responds (streaming):
   "Hey Sarah, I love that you're asking about creativity!
   With Mercury in Pisces today, your imagination is..."

4. User reads response, asks follow-up:
   "Should I start that painting project I've been thinking about?"
   → Backend uses previous context + new question
   → Knows user is interested in creative projects

5. Conversation continues...
```

## Testing

### Test with Sample Questions

```bash
# Get daily horoscope first
curl -X POST https://us-central1-arca-backend.cloudfunctions.net/get_daily_horoscope \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json"

# Ask question
curl -X POST https://us-central1-arca-backend.cloudfunctions.net/ask_the_stars \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How can I make the most of today?",
    "horoscope_date": "2025-01-24"
  }'
```

## Performance

- **Entity extraction:** ~1500-2000ms
- **Answer generation (streaming):** ~1500-2500ms (first chunk arrives in ~500ms)
- **Total latency:** ~3-4 seconds for complete answer

## Security

- ✅ **Authentication required** - Firebase ID token in Authorization header
- ✅ **User isolation** - Users can only access their own horoscopes/conversations
- ✅ **Rate limited** - Firebase Cloud Functions max instances prevent abuse
- ✅ **Input validation** - Question length limited to 500 characters

## Future Enhancements (Not Yet Implemented)

- Voice input for questions
- Image/screenshot sharing ("What does this mean?")
- Daily question suggestions based on user patterns
- Conversation analytics (most asked topics)

## Support

For questions or issues with Ask the Stars integration:
- Check Firestore logs in Firebase Console
- Review CloudWatch logs for function errors
- Contact backend team with `conversation_id` for debugging
