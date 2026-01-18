# AI Agent & Gallery System Documentation

## Claude API Configuration

### Model Selection (SINGLE SOURCE OF TRUTH)

The Claude model is configured in ONE place only: **`backend/app/config.py`**

```python
# backend/app/config.py - THE ONLY PLACE TO CHANGE THE MODEL
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
CLAUDE_MAX_TOKENS = 16384
CLAUDE_MAX_ITERATIONS = 25

# Available models for prompt caching:
# - claude-sonnet-4-5-20250929 (recommended - best price/performance)
# - claude-opus-4-20250514 (most capable, expensive)
# - claude-haiku-3-5-20241022 (fastest/cheapest)
```

All other files import from this config:
- `backend/app/services/agent_service.py` - Imports `CLAUDE_MODEL`, `CLAUDE_MAX_TOKENS`, `CLAUDE_MAX_ITERATIONS`
- `agent_runner.py` - Imports with fallback for standalone CLI use
- `agent_tools.py` - Imports with fallback for standalone CLI use

**To change the model:** Edit `backend/app/config.py` and restart the backend. That's it.

### Prompt Caching
We use Anthropic's prompt caching for 90% cost reduction on repeated content:

- **Tools**: Cached via `cache_control` on last tool definition
- **System prompt**: Cached as separate block
- **Memory context**: Cached separately (allows updates without invalidating system cache)

Cache pricing (Claude Sonnet 4.5):
- Base input: $3/MTok
- Cache write: $3.75/MTok (1.25x, one-time)
- Cache read: $0.30/MTok (0.1x, 90% savings!)

Monitor cache usage in logs:
```
📊 Cache: read=4500, created=0, uncached=50
```

### Key Files
- `backend/app/config.py` - **SINGLE SOURCE** for CLAUDE_MODEL constant
- `backend/app/services/agent_service.py` - Main agent service (imports from config)
- `agent_runner.py` - CLI agent runner (imports from config with fallback)
- `agent_tools.py` - Tool definitions (imports from config with fallback)

## Agent Memory System

The agent has a persistent memory system in `/memory/` that survives across sessions:

**Memory Files:**
```
/memory/
  ├── current_project.json     # Active project ID + session summary
  ├── conversation_summary.txt # Rolling history of conversations
  ├── insights.txt             # Agent's learned preferences/patterns
  └── learnings/               # Category-specific learnings
      └── fonts.json           # Font preferences, etc.
```

**Memory Tools (available to the agent):**
| Tool | Purpose |
|------|---------|
| `get_session_context` | Load previous context at session start |
| `save_session_context` | Save project ID + summary before ending |
| `add_agent_insight` | Record learnings to insights.txt |
| `store_learning` | Save category-specific learnings |
| `get_learnings` | Retrieve past learnings |

**Session Continuity Protocol (in system prompt):**
1. Agent calls `get_session_context` at the START of every conversation
2. If there's a saved project, agent acknowledges it
3. Agent saves context with `save_session_context` before conversation ends
4. Agent records insights with `add_agent_insight` when learning preferences

**Example Flow:**
```
User: (starts new session)
Agent: (calls get_session_context)
       "Welcome back! Last time we were working on '5 Most Dangerous Men'..."

User: "Post it to TikTok"
Agent: (calls post_slideshow_to_tiktok)
       (calls save_session_context with summary)
```

## Agent Page Architecture (`/frontend/src/pages/Agent.tsx`)
The AI Agent page is a **full-page chat interface** with integrated gallery:

**Layout:**
- Uses full viewport height (`height: calc(100vh - 64px)`)
- Header with logo, status badge, and Chat/Gallery tabs
- Chat area with messages, tool calls, and slide previews
- Input bar fixed at bottom of chat area (NOT page bottom)
- Negative margins to break out of Layout padding

**Key Features:**
- **Tabs**: Chat tab for conversation, Gallery tab for all assets
- **Streaming**: Uses SSE for real-time Claude responses
- **Tool Calls**: Displays active tools while streaming
- **Slide Previews**: Shows generated slides inline in chat
- **Auto-save**: Slides automatically save to gallery when generated

**State Management:**
```typescript
const [activeTab, setActiveTab] = useState<'chat' | 'gallery'>('chat');
const [galleryFilter, setGalleryFilter] = useState<'all' | 'slides' | 'scripts' | 'drafts'>('all');
const { items: galleryItems, stats, addSlide } = useGallery();
```

## Gallery System

**Database Model (`/backend/app/models/gallery_item.py`):**
```python
class GalleryItem(Base):
    __tablename__ = "gallery_items"
    
    id = Column(String(36), primary_key=True)
    item_type = Column(String(50))  # 'slide', 'script', 'prompt', 'image', 'project'
    project_id = Column(String(36), nullable=True)
    slide_id = Column(String(36), nullable=True)
    title = Column(String(255))
    image_url = Column(String(500))
    font = Column(String(50))
    theme = Column(String(50))
    content_style = Column(String(50))
    extra_data = Column(JSON)  # NOTE: 'metadata' is reserved by SQLAlchemy!
    status = Column(String(50))  # 'complete', 'draft', 'failed'
    session_id = Column(String(36))
```

**⚠️ IMPORTANT**: Never use `metadata` as a column name in SQLAlchemy models - it's reserved!

**API Endpoints (`/backend/app/routers/gallery.py`):**
```bash
GET  /api/gallery                    # List all items (supports filtering)
POST /api/gallery                    # Create item
GET  /api/gallery/{id}               # Get single item
PUT  /api/gallery/{id}               # Update item
DELETE /api/gallery/{id}             # Delete item
DELETE /api/gallery                  # Clear all
GET  /api/gallery/stats/summary      # Get statistics
```

**Frontend Context (`/frontend/src/context/GalleryContext.tsx`):**
```typescript
// Uses TanStack Query for API sync
const { items, stats, addSlide, removeItem, hasItem, clearGallery } = useGallery();

// addSlide converts SlidePreviewData to GalleryItem automatically
await addSlide(slidePreviewData);
```

**Gallery Tab Filters:**
- All: Shows everything
- Slides: Only `item_type === 'slide'`
- Scripts: `item_type === 'script'` or `'prompt'`
- Drafts: `status === 'draft'`

## Agent Streaming Protocol

The agent uses Server-Sent Events (SSE) with these event types:

```typescript
type AgentStreamEvent =
  | { type: 'session'; session_id: string }
  | { type: 'text'; text: string }
  | { type: 'thinking'; text: string }
  | { type: 'tool_start'; tool_name: string; tool_input: Record<string, unknown> }
  | { type: 'tool_result'; tool_name: string; result: Record<string, unknown>; success: boolean }
  | { type: 'slide_preview'; slide: SlidePreviewData }
  | { type: 'done'; iterations: number; tool_count: number }
  | { type: 'error'; message: string };
```

**Usage in frontend:**
```typescript
cleanupRef.current = streamAgentMessage(
  message,
  sessionId,
  handleStreamEvent,  // Processes each event
  onError,
  onComplete
);
```

## Adding New Gallery Item Types

1. Update `item_type` enum in model (already flexible - just use new string)
2. Add filter option in Agent.tsx `galleryFilter` type
3. Add filter button in Gallery tab
4. Update `filteredGalleryItems` logic to handle new type

## Agent-Prepared Automation (Project Queue Mode)

The agent can create content projects upfront and queue them for automated execution. This gives the agent control over what content gets posted while the automation handles scheduling.

### How It Works

```
┌──────────────────────────────────────────────────────────────┐
│             Interactive Phase (You + Agent)                   │
│                                                               │
│  1. Brainstorm topics with the agent                         │
│  2. Agent creates projects with generate_script              │
│  3. Review and approve scripts                               │
│  4. Agent queues projects: queue_projects_for_automation     │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                 Scheduled Execution                           │
│                                                               │
│  • APScheduler fires at configured times                     │
│  • Gets next project from queue                              │
│  • Generates images for the project                          │
│  • Posts to TikTok/Instagram if enabled                      │
│  • Records run in AutomationRun table                        │
└──────────────────────────────────────────────────────────────┘
```

### Two Queue Modes

| Mode | Description | Behavior |
|------|-------------|----------|
| **Topics Queue** | List of topic strings | Generates script + images on each run |
| **Projects Queue** | List of project UUIDs | Only generates images (script already exists) |

When `project_ids` is populated, the automation uses Project Queue mode. Otherwise, it falls back to Topics Queue mode.

### Agent Tools for Project Queue

| Tool | Description |
|------|-------------|
| `queue_projects_for_automation` | Add pre-created projects to an automation's queue |
| `get_automation_queue_status` | View queue status, items, and progress |
| `skip_to_next_in_queue` | Skip current item without running |

### Example Agent Conversation

```
User: "Let's prepare content for next week"

Agent: I'll create 5 projects for your Daily Wisdom automation.
       [calls generate_script for each topic]
       [calls approve_script for each]
       [calls queue_projects_for_automation with all 5 project IDs]
       
       Done! 5 projects queued for your 9am automation:
       1. Marcus Aurelius and journaling
       2. Seneca's letters to Lucilius  
       3. Epictetus: From slave to sage
       4. The Stoic morning routine
       5. 5 philosophers who changed history
       
       The automation will generate images and post when scheduled.
```

### UI Queue Visualization

The Automations page shows:
- **Queue Mode Badge**: Purple "Project Queue Mode" badge when using projects
- **Queue Stats**: Shows total items, current position, remaining
- **Queue Modal**: View all items with status (completed/current/pending)
- **Skip Button**: Advance to next item without running

### API Endpoints

```bash
GET  /api/automations/{id}/queue           # Get queue status
POST /api/automations/{id}/queue/projects  # Add projects to queue
POST /api/automations/{id}/queue/skip      # Skip current item
DELETE /api/automations/{id}/queue/projects # Clear project queue
POST /api/automations/{id}/runs/{run_id}/post-now # Post completed run
```

### Post Now Feature

Completed runs can be posted immediately to social platforms:

```bash
POST /api/automations/{id}/runs/{run_id}/post-now?platform=tiktok
POST /api/automations/{id}/runs/{run_id}/post-now?platform=instagram
POST /api/automations/{id}/runs/{run_id}/post-now?platform=both
```

The Runs History modal shows Post Now buttons for unposted completed runs.

## Key Files for Agent/Gallery
- `/frontend/src/pages/Agent.tsx` - Main agent page with tabs
- `/frontend/src/context/GalleryContext.tsx` - Gallery state with API sync
- `/frontend/src/api/client.ts` - Gallery API functions
- `/backend/app/models/gallery_item.py` - Database model
- `/backend/app/routers/gallery.py` - API endpoints
- `/backend/app/routers/agent.py` - Agent chat endpoints
- `backend/app/services/agent_tools.py` - Agent tool definitions
- `backend/app/services/agent_service.py` - Main agent service

## Key Files for Automation System
- `/backend/app/models/automation.py` - Automation model with project_ids queue
- `/backend/app/models/automation_run.py` - Run history model
- `/backend/app/services/scheduler.py` - APScheduler service (handles both modes)
- `/backend/app/routers/automations.py` - API endpoints including queue management
- `/frontend/src/pages/Automations.tsx` - UI with queue visualization
