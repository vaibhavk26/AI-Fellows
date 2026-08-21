## Objective

Generate a **complete, implementation-ready database design document** for the capstone project.

The database design must be derived from and remain fully consistent with the project's approved requirements, architecture, technical design, API contracts, and development approach.

The resulting document will be used directly by developers to implement the database. **Do not produce a conceptual-only database design.**

---

## Reference Documents

Read and analyze **all** of the following documents before generating the database design:

* `docs/capstone-proposal.md`
* `docs/capstone-requirements.md`
* `docs/capstone-architecture.md`
* `docs/capstone-technical-design.md`
* `docs/capstone-development-runbook.md`
* `docs/capstone-api-design.md`

Treat these documents as the **source of truth**.

Where information overlaps, resolve inconsistencies using the following priority:

1. `capstone-requirements.md`
2. `capstone-architecture.md`
3. `capstone-technical-design.md`
4. `capstone-api-design.md`
5. `capstone-development-runbook.md`
6. `capstone-proposal.md`

If an inconsistency cannot be resolved from the documents, explicitly identify it in a **Design Decisions / Assumptions** section rather than silently inventing a solution.

---

# Database Design Requirements

## 1. Database Technology

Identify the database technology specified or implied by the technical architecture.

Document:

* Database engine
* Version, if specified
* Relational/document/vector database components, if applicable
* Database hosting/deployment approach
* Development/test/production considerations
* ORM or database-access technology, if specified
* Migration framework, if specified

Do not introduce a different database technology unless the reference documents explicitly allow it.

---

## 2. Domain and Data Model

Identify all persistent business entities required by the system.

For every entity, provide:

* Entity name
* Purpose
* Business meaning
* Primary key
* Attributes
* Data types
* Required/optional status
* Default values
* Business constraints
* Foreign keys
* Unique constraints
* Relationships with other entities
* Lifecycle/status fields where applicable
* Created/updated metadata
* Soft-delete requirements, if applicable

Avoid creating unnecessary tables merely for theoretical normalization.

---

## 3. Detailed Table Specifications

For **every database table**, provide a structured definition containing:

| Column | Data Type | Nullable | Default | Key/Constraint | Description |
| ------ | --------- | -------- | ------- | -------------- | ----------- |

Also specify:

* Primary key
* Foreign keys
* Unique constraints
* Check constraints
* Composite keys where required
* Generated/identity columns
* Enumerated/status values
* Cascading behavior
* Delete/update behavior

The design must contain **actual data types and constraints**, not descriptions such as "appropriate type" or "suitable length."

---

## 4. Relationships

Define all relationships between entities.

For each relationship specify:

* Parent entity
* Child entity
* Cardinality
* Optionality
* Foreign key
* Referential integrity behavior
* Delete behavior
* Update behavior

Cover:

* One-to-one
* One-to-many
* Many-to-many
* Associative/junction tables where required

Clearly identify how many-to-many relationships are physically implemented.

---

## 5. Entity Relationship Model

Provide a logical ER diagram using **Mermaid ER syntax**.

The diagram must:

* Include all core entities
* Show primary keys
* Show important foreign keys
* Show relationships and cardinality
* Be syntactically valid Mermaid
* Be consistent with the detailed table definitions

Do not create relationships in the diagram that are not represented in the table design.

---

## 6. API-to-Database Mapping

The database design **must be explicitly synchronized with**:

`docs/capstone-api-design.md`

For each API resource/major endpoint, identify:

* API resource
* HTTP operation
* Database table(s) involved
* Read/write operation
* Primary lookup key
* Foreign-key dependencies
* Important validation rules
* Transaction requirements, if applicable

Create an **API-to-Database Traceability Matrix**:

| API Endpoint / Operation | Database Table(s) | CRUD Operation | Key Fields | Important Constraints |
| ------------------------ | ----------------- | -------------- | ---------- | --------------------- |

Ensure that every persistent API resource has corresponding database support.

Identify any API fields that:

* Do not have a database mapping
* Require transformation
* Are calculated rather than persisted
* Are derived from multiple tables

---

## 7. Requirements-to-Database Traceability

Trace the database design back to:

`docs/capstone-requirements.md`

Create a matrix:

| Requirement ID | Requirement Summary | Database Entity/Table | Relevant Fields | Supporting Constraint/Logic |
| -------------- | ------------------- | --------------------- | --------------- | --------------------------- |

Every requirement involving persistent data must have a clear database implementation.

Identify any requirement that cannot be fully supported by the proposed schema.

---

## 8. Data Integrity and Validation

Define database-level integrity rules wherever appropriate.

Cover:

* NOT NULL constraints
* UNIQUE constraints
* CHECK constraints
* Foreign-key constraints
* Referential integrity
* Valid status values
* Valid date/time ranges
* Numeric boundaries
* Duplicate prevention
* Business-critical uniqueness rules

Clearly distinguish between:

**Database-enforced validation**
and
**Application/API-level validation**

Do not unnecessarily move critical integrity rules into application code if they can safely be enforced by the database.

---

## 9. Indexing Strategy

Define an implementation-ready indexing strategy.

For each index specify:

| Table | Index Name | Columns | Type | Purpose |
| ----- | ---------- | ------- | ---- | ------- |

Consider indexes required for:

* Primary keys
* Foreign keys
* API lookup operations
* Search/filter operations
* Sorting
* Frequently queried status fields
* Date-range queries
* Composite queries
* Uniqueness requirements

Do not create indexes merely because a column exists.

Explain the purpose of every non-trivial index.

---

## 10. Transaction and Concurrency Considerations

Identify operations that require transactional consistency.

Document:

* Transaction boundaries
* Multi-table operations
* Atomic operations
* Potential race conditions
* Concurrent update considerations
* Optimistic/pessimistic locking requirements, if applicable
* Idempotency considerations for API operations

Keep this appropriate to the capstone's actual complexity; do not introduce enterprise-level complexity unnecessarily.

---

## 11. Audit and History

Determine which entities require audit information.

Where applicable, define standard fields such as:

* `created_at`
* `created_by`
* `updated_at`
* `updated_by`

If the requirements require historical tracking, define:

* Audit table(s)
* Historical record structure
* Change tracking approach
* What events are captured
* Retention requirements

Do not introduce full audit/history tables unless justified by the reference documents or required for the system.

---

## 12. Security and Sensitive Data

Identify any sensitive, confidential, or personally identifiable data stored in the database.

For each such field, document:

* Data classification
* Why it is stored
* Access restrictions
* Encryption requirements
* Masking requirements
* Whether hashing/tokenization is appropriate
* Retention/deletion requirements

Ensure the database design is consistent with the security architecture.

**Do not expose secrets, credentials, API keys, or sensitive configuration values in the database design.**

---

## 13. Data Lifecycle

For entities with meaningful lifecycle states, define:

* Status values
* Initial state
* Valid state transitions
* Terminal states
* Deletion/archive behavior

Where appropriate, provide a state-transition table:

| Entity | Current State | Allowed Next State | Trigger |
| ------ | ------------- | ------------------ | ------- |

Do not invent lifecycle states that are not supported by the requirements.

---

## 14. Seed and Reference Data

Identify all required reference/master data.

For each required seed dataset specify:

* Table
* Purpose
* Required records/values
* Whether values are system-controlled or user-configurable
* Whether seed data is required during initial deployment

Provide concrete seed values wherever they are defined by the reference documents.

---

## 15. Migration and Initialization

Define the database initialization approach.

Include:

* Schema creation
* Migration strategy
* Migration ordering
* Seed-data loading
* Environment initialization
* Handling of future schema changes
* Rollback considerations

Ensure this aligns with `docs/capstone-development-runbook.md`.

---

## 16. Performance Considerations

Identify realistic performance considerations for the capstone.

Cover:

* Expected data volume assumptions
* High-frequency queries
* Large result sets
* Pagination requirements
* Search/filter patterns
* Potential N+1 query issues
* Appropriate indexing
* Aggregation/query considerations

Do not introduce premature optimization or unnecessary infrastructure.

---

## 17. Backup and Recovery

Document the database backup/recovery approach **only to the level required by the capstone architecture**.

Include, where applicable:

* Backup strategy
* Recovery strategy
* Data persistence expectations
* Development/test environment considerations

Do not invent enterprise-grade disaster-recovery requirements unless specified.

---

## 18. Database Naming Standards

Define and apply consistent conventions for:

* Tables
* Columns
* Primary keys
* Foreign keys
* Indexes
* Constraints
* Junction tables
* Timestamps
* Boolean fields
* Status fields

Use the same conventions throughout the entire document.

---

## 19. Complete Schema

Provide a consolidated schema representation suitable for developer implementation.

Where appropriate, include executable SQL DDL for:

* Table creation
* Primary keys
* Foreign keys
* Constraints
* Indexes
* Required seed/reference data

The SQL must be syntactically consistent with the selected database technology.

Do not provide pseudo-SQL.

If the project uses an ORM rather than direct SQL migrations, provide the database structure in the format appropriate to the project's technology while still documenting the resulting physical schema.

---

# Design Quality Rules

The generated design must satisfy all of the following:

* No placeholder tables
* No placeholder columns
* No vague data types
* No "TBD" unless the reference documents genuinely leave a decision unresolved
* No unnecessary entities
* No duplicate representations of the same business concept
* No orphan foreign keys
* No unexplained relationships
* No API resource without appropriate persistence support
* No persistent requirement without database traceability
* No contradiction with the architecture or technical design
* No contradiction with the API design
* No unnecessary enterprise complexity

Prefer **simple, maintainable, capstone-appropriate design** over over-engineering.

---

# Consistency Validation

Before producing the final document, internally validate the design against all reference documents.

Specifically verify:

* [ ] Every persistent requirement is represented
* [ ] Every required entity has a table
* [ ] Every table has a defined primary key
* [ ] Every foreign key references a valid entity
* [ ] Every relationship is consistent with the requirements
* [ ] API request/response fields have appropriate database mappings
* [ ] CRUD operations required by the API are supported
* [ ] Required validation rules are enforceable
* [ ] Required indexes are defined
* [ ] Security requirements are addressed
* [ ] Audit requirements are addressed where applicable
* [ ] Lifecycle requirements are represented
* [ ] Seed/reference data requirements are addressed
* [ ] Database technology matches the architecture
* [ ] Migration strategy matches the development runbook
* [ ] ER diagram matches the physical schema
* [ ] SQL/ORM definitions match the documented schema
* [ ] No unexplained assumptions remain

---

# Final Design Decisions

Include a concise section documenting important database design decisions.

For each decision provide:

* Decision
* Rationale
* Alternatives considered, where relevant
* Impact on implementation

Only include decisions that materially affect the database design.

---

# Final Deliverable Structure

Generate the document using this structure:

1. Database Design Overview
2. Database Technology
3. Design Principles
4. Domain/Data Model
5. Entity Definitions
6. Table Specifications
7. Relationships
8. Entity Relationship Diagram
9. API-to-Database Mapping
10. Requirements-to-Database Traceability
11. Data Integrity and Validation
12. Indexing Strategy
13. Transaction and Concurrency Considerations
14. Audit and History
15. Security and Sensitive Data
16. Data Lifecycle
17. Seed and Reference Data
18. Migration and Initialization
19. Performance Considerations
20. Backup and Recovery
21. Naming Standards
22. Complete Schema / DDL
23. Design Decisions and Assumptions
24. Database Implementation Checklist
25. Final Consistency Validation

---

# Output Requirements

* Output **only clean Markdown**.
* No introductory commentary outside the document.
* No generic database advice.
* No filler content.
* No unexplained assumptions.
* No placeholders.
* Use headings, tables, bullet points, and checkboxes where useful.
* Use valid Mermaid syntax for the ER diagram.
* Use valid database-specific SQL where SQL is provided.
* Ensure all sections are internally consistent.
* Ensure terminology exactly matches the reference documents wherever possible.
* Make the document **developer-ready and implementation-ready**.

## Output File

Create the final document as:

`docs/capstone-database-design.md`

