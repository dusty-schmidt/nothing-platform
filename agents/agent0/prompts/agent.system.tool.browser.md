### browser_agent:
Subordinate agent controlling a Playwright browser.

**Args:** `message` (task instructions), `reset` (true = new agent, false = continue existing)
- New task: reset true, describe full goal
- Follow-up: reset false, start with "Considering open pages..."
- Never say "wait for instructions" — end with a terminal action
- Downloads: /a0/tmp/downloads

Full docs: cat /a0/agents/agent0/prompts/tool-docs/browser.md
