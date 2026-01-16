# Database Documentation

## Overview
- **Engine**: SQLite with SQLAlchemy ORM
- **Database File**: `./philosophy_generator.db` (relative to working directory)
- **Config**: `backend/app/database.py` uses `settings.database_url`
- **Models**: Auto-create tables on startup via `Base.metadata.create_all()`

**⚠️ IMPORTANT**: The database path is RELATIVE (`sqlite:///./philosophy_generator.db`). 
When running from project root, it uses `./philosophy_generator.db` in root.
When running from `/backend/`, it would use `/backend/philosophy_generator.db`.
Always run uvicorn from project root to use the correct database.

## Database Schema

### `projects` - Main project/slideshow container
| Column | Type | Description |
|--------|------|-------------|
| `id` | VARCHAR(36) PK | UUID |
| `name` | VARCHAR(255) | Project display name |
| `topic` | TEXT | Full topic/prompt description |
| `content_type` | VARCHAR(50) | 'slideshow' or 'video' |
| `script_style` | VARCHAR(50) | 'list', 'narrative', 'mentor_slideshow', 'wisdom_slideshow' |
| `status` | VARCHAR(50) | 'draft', 'script_review', 'script_approved', 'generating', 'complete', 'error' |
| `script_approved` | VARCHAR(1) | 'Y' or 'N' |
| `settings` | JSON | `{"image_model": "gpt15", "font": "bebas", "theme": "dark"}` |
| `created_at` | DATETIME | |
| `updated_at` | DATETIME | |

### `slides` - Individual slides within a project
| Column | Type | Description |
|--------|------|-------------|
| `id` | VARCHAR(36) PK | UUID |
| `project_id` | VARCHAR(36) FK | References projects.id |
| `order_index` | INTEGER | 0-based slide order |
| `title` | TEXT | Main text (often ALL CAPS) |
| `subtitle` | TEXT | Secondary text |
| `visual_description` | TEXT | AI image prompt |
| `narration` | TEXT | Voice-over script (if applicable) |
| `background_image_path` | VARCHAR(500) | AI-generated background (no text) |
| `final_image_path` | VARCHAR(500) | Background + text overlay |
| `video_clip_path` | VARCHAR(500) | For video projects |
| `current_font` | VARCHAR(50) | 'tiktok-bold', 'bebas', etc. |
| `current_theme` | VARCHAR(50) | 'oil_contrast', 'golden_dust', etc. |
| `current_version` | INTEGER | Version number for history |
| `image_status` | VARCHAR(50) | 'pending', 'generating', 'complete', 'error' |
| `error_message` | TEXT | Error details if failed |
| `created_at` | DATETIME | |
| `updated_at` | DATETIME | |

### `slide_versions` - Version history for slides
| Column | Type | Description |
|--------|------|-------------|
| `id` | VARCHAR(36) PK | UUID |
| `slide_id` | VARCHAR(36) FK | References slides.id |
| `version_number` | INTEGER | 1, 2, 3... |
| `title`, `subtitle`, `visual_description`, `narration` | TEXT | Snapshot of content |
| `font`, `theme` | VARCHAR(50) | Font/theme used |
| `background_image_path`, `final_image_path` | VARCHAR(500) | Image paths |
| `change_type` | VARCHAR(50) | 'initial', 'text_edit', 'font_change', 'theme_change', 'regenerate', 'revert' |
| `change_description` | TEXT | Human-readable description |
| `version_metadata` | JSON | Additional data |
| `created_at` | DATETIME | |

### `automations` - Scheduled content generation
| Column | Type | Description |
|--------|------|-------------|
| `id` | VARCHAR(36) PK | UUID |
| `name` | VARCHAR(255) | Automation name |
| `content_type` | VARCHAR(50) | 'wisdom_slideshow', 'mentor_slideshow', etc. |
| `image_style` | VARCHAR(50) | 'classical', 'cinematic', etc. |
| `topics` | JSON | List of topics to cycle through |
| `current_topic_index` | INTEGER | Current position in topics list |
| `schedule_times` | JSON | ['09:00', '14:00'] |
| `schedule_days` | JSON | ['mon', 'tue', 'wed', 'thu', 'fri'] |
| `status` | VARCHAR(50) | 'idle', 'running', 'paused' |
| `is_active` | BOOLEAN | Whether automation is enabled |
| `last_run`, `next_run` | DATETIME | Timing |
| `total_runs`, `successful_runs`, `failed_runs` | INTEGER | Stats |
| `email_enabled` | BOOLEAN | Send notifications |
| `email_address` | VARCHAR(255) | Notification email |
| `settings` | JSON | Additional settings |
| `config` | JSON | Legacy config field |
| `created_at`, `updated_at` | DATETIME | |

### `automation_runs` - History of automation executions
| Column | Type | Description |
|--------|------|-------------|
| `id` | VARCHAR(36) PK | UUID |
| `automation_id` | VARCHAR(36) FK | References automations.id |
| `topic` | VARCHAR(500) | Topic used for this run |
| `status` | VARCHAR(50) | 'running', 'success', 'error' |
| `started_at`, `completed_at` | DATETIME | Timing |
| `duration_seconds` | INTEGER | How long it took |
| `project_id` | VARCHAR(36) | Created project ID |
| `slides_count` | INTEGER | Number of slides generated |
| `image_paths` | JSON | List of generated image paths |
| `tiktok_posted` | BOOLEAN | Whether posted to TikTok |
| `tiktok_publish_id` | VARCHAR(100) | TikTok's publish ID |
| `error_message`, `error_details` | TEXT/JSON | Error info |
| `created_at` | DATETIME | |

### `gallery_items` - Agent gallery for saved content
| Column | Type | Description |
|--------|------|-------------|
| `id` | VARCHAR(36) PK | UUID |
| `item_type` | VARCHAR(50) | 'slide', 'script', 'prompt', 'image', 'project' |
| `project_id`, `slide_id` | VARCHAR(36) | Optional references |
| `title`, `subtitle`, `description` | TEXT | Content |
| `image_url`, `thumbnail_url` | VARCHAR(500) | Image URLs |
| `font`, `theme`, `content_style` | VARCHAR(50) | Styling info |
| `extra_data` | JSON | Additional metadata (NOT 'metadata' - reserved!) |
| `status` | VARCHAR(50) | 'complete', 'draft', 'failed' |
| `session_id` | VARCHAR(36) | Agent session that created it |
| `created_at`, `updated_at` | DATETIME | |

### `generation_logs` - API call/cost tracking
| Column | Type | Description |
|--------|------|-------------|
| `id` | VARCHAR(36) PK | UUID |
| `project_id` | VARCHAR(36) FK | Optional reference |
| `action` | VARCHAR(100) | 'generate_image', 'generate_script', etc. |
| `model_used` | VARCHAR(100) | 'gpt15', 'claude-sonnet-4-5', etc. |
| `details` | JSON | Request/response details |
| `cost` | FLOAT | Estimated cost in USD |
| `tokens_used` | INTEGER | Token count |
| `success` | BOOLEAN | Whether it succeeded |
| `error_message` | TEXT | Error if failed |
| `created_at` | DATETIME | |

## Database Migrations

SQLite doesn't support all ALTER TABLE operations. For adding columns:

```bash
# Add a column with default value
sqlite3 philosophy_generator.db "ALTER TABLE projects ADD COLUMN new_column VARCHAR(50) DEFAULT 'value';"

# Verify
sqlite3 philosophy_generator.db "PRAGMA table_info(projects);"
```

For complex migrations (rename column, change type), you need to:
1. Create new table with correct schema
2. Copy data from old table
3. Drop old table
4. Rename new table

## Common Database Operations

```bash
# Check table schema
sqlite3 philosophy_generator.db "PRAGMA table_info(slides);"

# List all tables
sqlite3 philosophy_generator.db ".tables"

# Query project with slides
sqlite3 philosophy_generator.db "SELECT p.name, COUNT(s.id) as slides FROM projects p LEFT JOIN slides s ON p.id = s.project_id GROUP BY p.id;"

# Copy data between databases
sqlite3 philosophy_generator.db << 'EOF'
ATTACH DATABASE 'backend/philosophy_generator.db' AS other;
INSERT INTO slides SELECT * FROM other.slides WHERE project_id = 'uuid';
DETACH DATABASE other;
EOF
```

## Model Files
- `backend/app/models/project.py` - Project model
- `backend/app/models/slide.py` - Slide model with versioning
- `backend/app/models/automation.py` - Automation model
- `backend/app/models/gallery_item.py` - Gallery model

**⚠️ CRITICAL**: Never use `metadata` as a column name - it's reserved by SQLAlchemy!
