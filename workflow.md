# Version-1 Deterministic Workflow (Python-First Architecture)

This workflow keeps **LLM hallucination risk low** by assigning deterministic tasks to **Python** and creative/generative tasks to **LLMs**.  
This follows the **prompt-chaining pipeline pattern**, where outputs from one step are passed to the next step as structured JSON. ([promptingguide.ai](https://www.promptingguide.ai/techniques/prompt_chaining?utm_source=chatgpt.com "Prompt Chaining"))

---
# Core Principle

**Python does:**
- file handling
- schema validation
- keyword deduplication
- state management
- deterministic formatting
- workflow control

**LLM does:**
- language generation
- marketing copy
- semantic keyword expansion
- visual prompt design

---
# SYSTEM STATE FILE
```text
workflow_state.json
```
Python updates this after every step.

---
# STEP-BY-STEP WORKFLOW

---
# STEP 0 — Python Initialization

**Python performs:**
```text
1 load product images
2 load raw product data
3 create empty workflow_state.json
4 validate input files
```

**Output:**
```json
workflow_state.json
```

---
# STEP 1 — PROMPT 1A
Product Data Extraction

LLM task:
```text
extract structured product dataset
```

Python then:
```text
validate JSON
save to workflow_state.json
```

---
# STEP 2 — PROMPT 1B
Visual Product Identity Extraction

LLM task:
```text
extract visual_identity
object_layout_map
product_geometry
```

Python:
```text
validate schema
append to workflow_state.json
```

---
# STEP 3 — PROMPT 2
Amazon Title

LLM:
```text
generate title
```

Python:
```text
check 200 char limit
check duplicate words
save
```

---
# STEP 4 — PROMPT 3
Bullet Points

LLM:
```text
generate 5 bullets
```

Python:
```text
enforce bullet count
remove duplicates
save
```

---
# STEP 5 — PROMPT 4
Product Description

LLM:
```text
generate description
```

Python:
```text
check word length
save
```

---
# STEP 6 — PROMPT 5
Backend Keywords

LLM:
```text
generate keywords
```

Python:
```text
remove words from title
remove duplicates
validate spacing
save
```

---
# STEP 7 — PROMPT 6
Customer Search Intent

LLM:
```text
generate keyword clusters
```

Python:
```text
deduplicate
normalize
save
```

---
# STEP 8 — PROMPT 7

A+ Content

LLM:
```text
generate brand story
feature modules
```

Python:
```text
validate JSON
save
```

---
# STEP 9 — PROMPT 8
Technical Specifications

Python performs most of the work:
```text
convert attributes → spec table
```

LLM only fills gaps if necessary.

---
# STEP 10 — PROMPT 9
Customer FAQ

LLM:
```text
generate FAQs
```

Python:
```text
validate count
save
```

---
# STEP 11 — PROMPT 10
Social Posts

LLM:
```text
generate captions
```

Python:
```text
validate hashtag count
save
```

---
# IMAGE PIPELINE

---
# STEP 12 — PROMPT 11
Image 1 Prompt

LLM:
```text
generate hero image prompt
```

Python:
```text
save image_strategy
```

---
# STEP 13 — PROMPT 12
Image 1 Generation

LLM:
```text
generate image prompt
```

Python:
```text
extract style_lock
save style_lock
```

---
# STEP 14 — PROMPT 13
Image 2 Prompt

LLM:
```text
generate feature image prompt
```

---
# STEP 15 — PROMPT 14
Image 2 Generation

LLM generates image prompt.

Python saves result.

---
# STEP 16 — PROMPT 15
Image 3 Prompt

LLM generates prompt.

---
# STEP 17 — PROMPT 16
Image 3 Generation

Python saves output.

---
# STEP 18 — PROMPT 17
Image 4 Prompt

LLM generates prompt.

---
# STEP 19 — PROMPT 18
Image 4 Generation

Python saves output.

---
# STEP 20 — PROMPT 19
Image 5 Prompt

LLM generates prompt.

---
# STEP 21 — PROMPT 20
Image 5 Generation

Python saves output.

---
# STEP 22 — PROMPT 21
Image 6 Prompt

LLM generates prompt.

---
# STEP 23 — PROMPT 22
Image 6 Generation

Python saves output.

---
# STEP 24 — PROMPT 23
Image 7 Prompt

LLM generates prompt.

---
# STEP 25 — PROMPT 24

Image 7 Generation

Python saves output.

---
# FINAL OUTPUT

Python compiles final deliverables:
```text
amazon_listing.json
image_prompts.json
social_posts.json
workflow_state.json
```

---
# Why This Architecture Is Deterministic
Because:
```text
Python handles:
validation
deduplication
state control
```

and the LLM only handles **creative generation tasks**.

Breaking complex workflows into chained steps like this improves reliability and debugging because each step performs a single task and passes structured outputs to the next step. ([datalearningscience.com](https://datalearningscience.com/p/design-pattern-prompt-chaining-building?utm_source=chatgpt.com "1. Prompt Chaining - Building Step-by-Step AI Workflows"))

---
# Result
Version-1 system becomes a **deterministic LLM production pipeline**:

```text
input
↓
dataset extraction
↓
amazon listing generation
↓
marketing content
↓
image strategy
↓
image prompt generation
```

with **Python enforcing correctness at every step.**
