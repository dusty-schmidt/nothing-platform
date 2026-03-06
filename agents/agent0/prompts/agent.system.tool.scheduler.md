## Task Scheduler Subsystem:
Create, list, run, and manage scheduled/planned/adhoc background tasks.
Three types: `scheduled` (cron), `planned` (fixed datetimes), `adhoc` (manual).
!!! When asked to execute a task, check if it exists first — never create if it already exists.
Do not manually run scheduled/planned tasks after creating them.

**Tools:** `scheduler:list_tasks` `scheduler:find_task_by_name` `scheduler:show_task` `scheduler:run_task` `scheduler:delete_task` `scheduler:create_scheduled_task` `scheduler:create_adhoc_task` `scheduler:create_planned_task` `scheduler:wait_for_task`

**Key args (create):** `name`, `system_prompt`, `prompt`, `attachments`, `dedicated_context` (bool)
- scheduled: + `schedule` dict with keys `minute hour day month weekday` (cron syntax)
- planned: + `plan` list of ISO datetime strings
- run/delete/wait: `uuid` — get from list_tasks or find_task_by_name

Full docs: cat /a0/agents/agent0/prompts/tool-docs/scheduler.md
