# Competitive & Ecosystem Analysis

This document evaluates the state of AI tooling, agent systems, and prompt management in 2025/2026, articulating the distinct architectural gap addressed by the **AI Skill Protocol (ASP)**.

---

## 1. Overview of Existing Approaches

| System / Standard | Core Problem Solved | What It Does NOT Solve | ASP Differentiation |
|---|---|---|---|
| **Model Context Protocol (MCP)** | Unified tool & resource connectivity for AI clients (N×M problem for I/O) | Reusable skill packaging, versioning, semver dependency chains, evaluation criteria | **Complementary**: ASP leverages MCP Prompts as a downstream distribution transport |
| **LangChain / LlamaIndex / CrewAI** | Frameworks for orchestrating agent loops, memory, and tool execution | Cross-framework interoperability; skills cannot be shared outside framework runtime | **Framework Neutral**: Skills defined in ASP run in LangChain, raw SDKs, Claude, or Gemini |
| **OpenAI Assistants / Custom GPTs** | Hosted, managed assistant configurations within a single ecosystem | Multi-model portability, vendor independence, local execution, git-based versioning | **Open Standard**: Zero proprietary vendor lock-in |
| **Prompt Registries (PromptHub, etc.)** | Centralized web repositories for raw text prompts | Typed input/output contracts, package management, lockfiles, dependency trees | **Protocol First**: Treats skills as software packages, not static text snippets |
| **Hugging Face Hub** | Model weights, datasets, and space deployments | Fine-grained skill logic, agent instruction contracts, lightweight packaging | **Package Level**: Focuses on the behavioral skill layer above models and below frameworks |
| **Package Managers (npm, Cargo, pip)** | Dependency resolution and distribution for executable software | AI-specific concerns (prompts, model capabilities, token limits, prompt injection) | **AI-Native Adaptation**: Applies package management rigor to prompt/skill engineering |

---

## 2. In-Depth Comparison

### 2.1 Model Context Protocol (MCP) vs. ASP

* **What MCP is**: Released by Anthropic in late 2024 and adopted across the industry, MCP defines a client-host-server protocol (over JSON-RPC 2.0) allowing models to interact with local/remote data and tools.
* **The Gap**: MCP standardizes *how an AI calls an external API or reads a file*. It does *not* standardize how an author bundles instructions, evaluation suites, capability constraints, and dependencies into a shareable package.
* **How They Intersect**: ASP does not replace MCP. Instead, ASP serves as the *package manager and packaging specification* for skills, and uses MCP's `prompts` interface as an execution conduit into tools like Claude Code and Gemini CLI.

### 2.2 Orchestration Frameworks vs. ASP

* **What Frameworks do**: LangChain, LlamaIndex, Semantic Kernel, and AutoGen provide runtime engines to construct agent graphs.
* **The Gap**: If an enterprise writes 50 specialized analysis skills in LangChain, they cannot use them in a native Gemini CLI workflow or Claude Code without maintaining duplicate prompt definitions.
* **How They Intersect**: ASP skills define declarative contracts. A LangChain adapter can ingest an ASP skill package just as easily as an MCP server or a standalone Python script.

---

## 3. The Missing Primitive: The "Skill" as a Portable Software Package

Until now, software engineering had package managers for code (`npm`, `pip`, `cargo`, `maven`), container standards for execution environments (`OCI`, `Docker`), and protocol standards for tool interfaces (`MCP`, `OpenAPI`).

However, **reusable AI behaviors** remained stuck in copy-pasted Markdown files, company wikis, or proprietary SaaS dashboards.

ASP introduces the missing primitive:
1. **Machine-validated interface contract**: Inputs and outputs governed by JSON Schema Draft 2020-12.
2. **Deterministic lockfiles**: `skill.lock` with SHA-256 integrity pinning.
3. **Decentralized distribution**: Works out-of-the-box over standard Git repositories without needing a centralized registry.
4. **Sandboxed permission declarations**: Explicit declaration of network, filesystem, and code execution requirements.
