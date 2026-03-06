#!/bin/bash
# GOB Prompt Setup — run after container rebuild
# Creates symlinks so session.md relative includes resolve

PROMPTS=/a0/agents/agent0/prompts
ln -sf /a0/usr/gob_session_override.md $PROMPTS/gob_session_override.md
ln -sf /a0/agents/agent0/_context.md $PROMPTS/_context.md
echo "GOB prompt symlinks created"
