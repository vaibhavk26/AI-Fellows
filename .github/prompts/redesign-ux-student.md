I want you to redesign the **Student module** in my Streamlit app to match a modern, minimalist, EdTech‑grade UX, similar to the Teacher module redesign.  
Do **not** modify backend logic, database operations, or API calls.  
Do **not** break existing exam workflows.  
Only reorganize UI and UX.

**IMPORTANT:**  
Preserve the existing **GitHub Dark theme**, color palette, spacing, and typography used throughout the application.  
All redesigned Student pages must visually align with the current global theme.

---

## 🎯 Goal
Transform the Student experience into a clean, structured, multi‑page module with a landing hub and dedicated sub‑pages.

---

## 📌 Required New Structure

### 1. **Student Hub (Landing Page)**
Create a clean landing page with three large navigation cards:

- Dashboard (Student analytics & progress)  
- Exam (Attempt exam)  
- Results (View exam results & explanations)  

Each card should include:
- Title  
- Short description  
- Optional icon  
- A “Go to page” button  

The landing page must be minimalist and distraction‑free.

---

### 2. **Dashboard Page (Student Analytics)**
Move all student analytics here:

- Progress overview  
- Completed exams  
- Scores  
- Strengths & weaknesses  
- Trend charts  

Use cards, metric blocks, and small charts.  
No clutter.

---

### 3. **Exam Page (Attempt Exam)**
Redesign the exam-taking interface:

- Clean question card  
- Clear option buttons  
- Timer panel  
- Progress indicator (e.g., “Q1 of 10”)  
- Next/Previous navigation  
- Submit confirmation modal  

Ensure the exam workflow remains fully functional.

---

### 4. **Results Page (Detailed Breakdown)**
Move all results content here:

- Score summary  
- Time taken  
- Accuracy  
- Topic-wise performance  
- Question-by-question breakdown  
- Explanation for incorrect answers  

Use collapsible cards, color-coded correctness, and clean spacing.

---

## 🎨 UX Style Requirements
Apply a modern EdTech aesthetic while **preserving the existing GitHub Dark theme**:
- Minimalist layout  
- Clean spacing  
- No long scrolls  
- Use cards, tabs, containers  
- Consistent padding  
- Maintain current dark color palette  
- Maintain current typography  
- Ensure redesigned pages visually match the rest of the app  

---

## 🛠️ Implementation Notes
- Reuse existing backend logic and exam functions.  
- Do not break exam submission, scoring, or result generation.  
- Only reorganize UI and UX.  
- Keep code modular and readable.  
- Create new files if needed (e.g., `student_hub.py`, `student_dashboard.py`, etc.).  
- Ensure navigation works smoothly from the persona‑aware sidebar.  
- Ensure all new pages inherit the existing theme and styling conventions.

---

## 🎯 Final Deliverable
Refactor the Student module so that:
- The landing page is clean and modern  
- Each workflow has its own dedicated sub‑page  
- No clutter  
- No long scrolling  
- UX feels like a professional EdTech platform  
- All pages remain fully aligned with the existing GitHub Dark theme and typography  

Make all necessary UI changes across the Streamlit app to implement this redesign.
