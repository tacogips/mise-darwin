---
name: swift-coding
description: Use when writing or reviewing Swift code, especially Codable DTOs, CLI/API result models, state machines, discriminators, provenance fields, or public library contracts.
metadata:
  short-description: Swift API and DTO coding rules
---

# Swift Coding

Apply these rules before editing Swift:

- Model closed value sets as enums, not raw `String` fields. Use `enum Name: String, Codable, Equatable, Sendable` when a value is serialized as text.
- Use raw strings only for genuinely open user data, external identifiers, free-form messages, paths, command output, or provider-owned values.
- For public DTOs, make provenance and state fields typed (`enum`) when the producer controls the allowed values.
- Keep wire compatibility by giving enums stable raw values such as `"workflow"` or `"package"`; use `.rawValue` only at text/table rendering boundaries.
- Add tests that assert the typed enum value, not only the encoded string.
- Prefer small explicit DTOs over dictionaries when fields are known.
