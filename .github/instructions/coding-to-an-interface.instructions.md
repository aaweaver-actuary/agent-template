---
description: Always code to an interface, not an implementation. This means defining clear interfaces and data contracts before implementing the internal logic of components.
---

## Coding to an Interface Instructions

### When to Load These Instructions
Load these instructions whenever you are generating code, designing new features, or reviewing architectural changes. They are especially important at the start of a new module, service, or when integrating multiple components.

### Core Principles
1. **Define Interfaces and Data Contracts First:**
	- Begin by specifying the interfaces (APIs, function signatures, class contracts) and the data structures that will be exchanged between different parts of the codebase.
	- Prioritize clear, minimal, and stable boundaries between components.

2. **Wire Up a Simple End-to-End Version:**
	- Once interfaces and data contracts are defined, create a simple, fully-wired version of the system that connects all the pieces, even if the internal logic is just placeholders or stubs.
	- This validates the architecture and ensures all parts communicate as expected.

3. **Iteratively Fill in Implementation Details:**
	- After the system is wired up and interfaces are validated, proceed to implement the internal logic and details of each component.
	- This approach reduces rework and makes it easier to adapt to changes in requirements or design.

### Summary
Always start by defining interfaces and data contracts, then wire up a working skeleton, and only then proceed to detailed implementation. This ensures a robust, maintainable, and adaptable codebase.