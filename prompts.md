### PROMPT-1 : requirement generation

Using the docs/capstone-proposal.md document, generate a requirements document.

Guidelines:
		- start with short capstone introduction
		- add requirements index table for traceability
		- apply logical grouping to the requirements as appropriate
		- categorise requirements in to Must Have / Should Have / Could Have
		- Have two clear sections - functional requirements and non-functional requirements
		- output file name : docs/capstone-requirements.md
---

### PROMPT-2 : architecture generation

Using the docs/capstone-proposal.md and docs/capstone-requirements.md documents, generate an architecture document.

Guidelines:
		- start with short capstone introduction
		- architecture diagram and supporting details
		- architecture should be simple for capstone MVP
		- architecture should be modular and flexible to support future evolution 
		- output file name : docs/capstone-architecture.md
---

### PROMPT-3 : Design generation

Using the docs/capstone-proposal.md, docs/capstone-requirements.md, and docs/capstone-architecture.md documents, generate a detailed technical design document.

Guidelines:
		- start with short capstone introduction
		- python as a base language
		- consider open source / free libraries, tools and technology wherever possible
		- output file name : docs/capstone-technical-design.md

---
### PROMPT-4 : Implementation Plan generation

Using the following reference documents, generate a detailed implementation plan for the capstone project.

Reference Documents:
- docs/capstone-proposal.md
- docs/capstone-requirements.md
- docs/capstone-architecture.md
- docs/capstone-technical-design.md

Guidelines: 
- clean, structured Markdown implementation plan
- including detailed tasks and deliverables 
- Logical sequencing (dependencies first)
- include recommended tools, libraries, dependencies, models etc 
- include recommended project structure


Output Formatting requirements
- Output MUST be in clean Markdown  
- Use headings, subheadings, bullet points, and checkboxes  
- No filler text  
- No generic advice  
- The plan must be actionable and ready for execution  
- Output File Name : docs/capstone-implementation-plan.md


### PROMPT-5 : API Design generation 
**Task:**  
Generate a detailed API design document for the capstone project.

**Reference Documents:**  
- `docs/capstone-proposal.md`  
- `docs/capstone-requirements.md`  
- `docs/capstone-architecture.md`  
- `docs/capstone-technical-design.md`  
- `docs/capstone-development-runbook.md`  

**Guidelines:**  
- Produce a clean, structured, detailed API design document.  
- Base the design on a FastAPI implementation.  
- Ensure the design is actionable and ready for implementation (no placeholders or vague text).  
- Incorporate endpoints, request/response schemas, authentication, error handling, and versioning strategy.  
- Align with the capstone architecture and requirements provided in the reference documents.  

**Output Formatting Requirements:**  
- Output MUST be in clean Markdown.  
- Use headings, subheadings, bullet points, and checkboxes where appropriate.  
- No filler text.  
- No generic advice.  
- The document should be developer-ready.  

**Output File Name:**  
`docs/capstone-api-design.md`
