## SHORT / ORIGINAL DESCRIPTION:

#### Implement a conversational agent that uses MCP to simulate dynamic memory by tracking and updating structured user-specific information and prefernces (develop custom tool for memory management). Need to identify and store long term (user-specific) and short term (chat-specific) separately.

## EXTENDED DESCRIPTION:

### 1. Project Goal

Build a conversational agent using MCP that:

- Stores long-term user memory across sessions
- Stores short-term session memory only for the active chat
- Uses custom MCP tools to read/write/update these memories

### 2. Core Features

#### Long-Term Memory (LTM)

- User preferences (tone, name, style)
- User's stable info (interests, background)
- Saved across sessions using a persistent store (JSON/SQLite)

#### Short-Term Memory (STM)

- Current task
- Current topic
- Soft, temporary preferences
- Reset after conversation ends

### 3. System Architecture

**Agent (LLM)**

**MCP Memory Tool Server**

- `/read_ltm`
- `/write_ltm`
- `/read_stm`
- `/write_stm`
- `/clear_stm`

**Storage**

- LTM → JSON file or SQLite
- STM → In-memory or temp JSON

### 4. Tool Design

#### Long-Term

- `memory.ltm_read`
- `memory.ltm_write`
- `memory.ltm_update`
- `memory.ltm_clear`

#### Short-Term

- `memory.stm_read`
- `memory.stm_write`
- `memory.stm_clear`

### 5. Agent Behavior Rules

- If user gives personal preference → store in LTM
- If user gives instructions for the current task → store in STM

**Before responding:**
→ Read both LTM and STM

**After each message:**
→ Update memory when required
