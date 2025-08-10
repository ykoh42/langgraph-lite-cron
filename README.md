# ⏰ LangGraph Lite Cron

- A free, self-hosted alternative to LangGraph Platform's Cron Jobs with the same API interface (compatible with [
  `langgraph-sdk`](https://pypi.org/project/langgraph-sdk/)).
- Designed for use with [ambient agents](https://blog.langchain.com/introducing-ambient-agents/) to enable scheduled and
  recurring tasks.

**Requirements:** Python 3.9+, PostgreSQL, Redis

> ⚠️ **Warning: Early development. Not for production use.**

## ⚡ Quick Start

### 1. Install

```sh
pip install langgraph-lite-cron
```

### 2. Add Custom Routes

Add cron routes to your FastAPI app (e.g., `./src/agent/webapp.py`):

```python
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from langgraph_lite_cron import crons
from langgraph_lite_cron.scheduler import create_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    async with create_scheduler() as scheduler:
        await scheduler.start_in_background()
        app.state.scheduler = scheduler

        yield

        await scheduler.stop()
        await scheduler.wait_until_stopped()


app = FastAPI(lifespan=lifespan)
app.include_router(crons.router)
```

### 3. Configure langgraph.json

Update your `langgraph.json` to include the custom app:

```json
{
    "dependencies": [
        "."
    ],
    "graphs": {
        "agent": "./src/react_agent/graph.py:graph"
    },
    "env": ".env",
    "image_distro": "wolfi",
    "http": {
        "app": "./src/agent/webapp.py:app"
    }
}
```

### 4. Deploy

Deploy using [Self-hosted Standalone Server](https://docs.langchain.com/langgraph-platform/deploy-standalone-server) with
Kubernetes, Docker and Docker Compose.

### 5. Use Cron API

```python
from langgraph_sdk import get_client

client = get_client(url="http://localhost:8123")

# Create thread
thread = await client.threads.create()

# Schedule job for thread (stateful)
cron_job = await client.crons.create_for_thread(
    thread["thread_id"],
    "agent",
    schedule="27 15 * * *",
    input={"messages": [{"role": "user", "content": "What time is it?"}]},
)

# Schedule job without thread (stateless)
cron_job_stateless = await client.crons.create(
    "agent",
    schedule="0 9 * * *",
    input={"messages": [{"role": "user", "content": "Good morning!"}]},
)

# List all cron jobs
crons = await client.crons.search(assistant_id="agent")

# Delete a specific job
await client.crons.delete(cron_job["cron_id"])

# Delete all jobs
for cron in crons:
    await client.crons.delete(cron["cron_id"])
```

## ⏱️ Cron Format

Standard cron format: `minute hour day month weekday`

- `0 9 * * *` - 9:00 AM daily
- `30 14 * * 1` - 2:30 PM every Monday
- `0 */4 * * *` - Every 4 hours

## 💡 Example Use Cases

- [executive-ai-assistant](https://github.com/langchain-ai/executive-ai-assistant) – An AI agent acting as an Executive
  Assistant
- [social-media-agent](https://github.com/langchain-ai/social-media-agent) – Generates Twitter and LinkedIn posts from a
  given URL with human-in-the-loop approval
- [agents-from-scratch](https://github.com/langchain-ai/agents-from-scratch) – Step-by-step tutorial for building an
  email agent with Gmail API, HITL, and memory
- [ff-take-bot](https://github.com/langchain-ai/ff-take-bot) – A “Take Bot” agent that runs in the background to keep a
  fantasy football league active
- [ambient-agent-101](https://github.com/langchain-ai/ambient-agent-101) – Learn LangGraph basics by building an ambient
  agent that manages Gmail
- [reddit-radar](https://github.com/langchain-ai/reddit-radar) – AI agent for detecting or analyzing Reddit posts
- [daily-brew](https://github.com/langchain-ai/daily-brew) – Automates publishing daily reflection content to a Slack
  channel
