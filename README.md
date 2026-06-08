# Jarvis 3

Clean modular rebuild of Jarvis using a brain → registry → agents → tools/providers architecture.

## Goal
Jarvis 3 is designed to be modular, agent-based, provider-swappable, UI/avatar-ready, testable, and scalable toward a future local app or SaaS-style architecture.

## Suggested first milestone
`0.1.0 — Core Boot + Agent Registry + Event System`

Jarvis should be able to boot, load config, register enabled agents, accept a text command, route it to a mock/basic agent, return a standard result object, write a debug log, and pass tests.
