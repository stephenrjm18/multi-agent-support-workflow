# Multi-Agent Customer Support Automation Platform

A GenAI-powered customer support workflow that combines specialized agents, deterministic business logic, human approval, QA validation, and retry/rework using LangGraph.

## Live Demo

Frontend:

https://multi-agent-support-workflow-6qm2tjn8i-stephen-a077.vercel.app

Backend:

https://multi-agent-support-backend.onrender.com

Health Check:

https://multi-agent-support-backend.onrender.com/health

> The demo is intended for portfolio demonstration. The backend uses SQLite with synthetic data and is deployed using free hosting infrastructure.

---

## Project Overview

Customer support workflows often require multiple steps rather than a single LLM response.

For example, a refund request may require the system to:

1. Understand the customer's request.
2. Identify the issue type.
3. Investigate customer and order information.
4. Determine whether the requested action is allowed.
5. Generate a resolution proposal.
6. Request human approval when required.
7. Validate the proposed resolution.
8. Rework the resolution if QA fails.
9. Generate the final customer response.

This project implements that workflow as a stateful LangGraph application.

The system uses specialized agents instead of allowing one LLM call to control the entire process.

---

## Problem Statement

A simple LLM chatbot can generate a response to a customer request, but real support workflows often require:

- access to structured customer data
- business-rule validation
- controlled actions
- human approval
- output validation
- retry and correction
- persistent workflow state

The goal of this project is to demonstrate how an LLM can be integrated into a controlled application workflow rather than being given unrestricted control over business operations.

---

## Architecture

```text
                         ┌──────────────────────┐
                         │   Next.js Frontend   │
                         │   React + TypeScript  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      FastAPI         │
                         │      REST API        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      LangGraph       │
                         │  Stateful Workflow   │
                         └──────────┬───────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             ▼                      ▼                      ▼
       Triage Agent        Investigation Agent      Resolution Agent
                                                           │
                                                           ▼
                                                  Human Approval
                                                           │
                                                           ▼
                                                     QA Agent
                                                           │
                                             ┌─────────────┴─────────────┐
                                             │                           │
                                           Pass                         Fail
                                             │                           │
                                             ▼                           ▼
                                      Response Agent              Retry / Rework
                                             │                           │
                                             ▼                           │
                                      Final Response                     │
                                                                         │
                                                                  Resolution Agent