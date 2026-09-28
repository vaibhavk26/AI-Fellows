I want you to refactor and redesign the existing **Teacher page** in my Streamlit app to implement a modern, minimalist, EdTech‑grade UX.  
Do **not** modify other pages such as Home, Dashboard, Exam, Results, or Generate.  
Focus **only** on the Teacher module.

**IMPORTANT:**  
Preserve the **existing GitHub Dark theme and typography** used throughout the application.  
All redesigned Teacher pages must visually align with the current global theme, color palette, spacing, and typographic style already implemented in the app.

---

## 🎯 Goal
Transform the current long, cluttered Teacher page into a clean, multi‑page Teacher module with a landing hub and dedicated sub‑pages.  
Use the most appropriate navigation approach based on the existing codebase (e.g., multipage folder structure, `st.switch_page`, or tabs).

---

## 📌 Required New Structure

### 1. **Teacher Landing Page (Hub)**
Create a clean landing page with four large navigation cards:

- Teacher Analytics  
- Student Roster  
- Assessments  
- Question Bank  

Each card should include:
- Title  
- Short description  
- Optional icon  
- A “Go to page” button  

The landing page must be minimalist and distraction‑free.

---

### 2. **Teacher Analytics Page**
Move all analytics content here:

- Question Bank Metrics: Validated, Generated, Rejected  
- Assessment Analytics: Assigned, Started, Completed, Average Score  
- Exam Records Table  

Use cards, metric blocks, or small charts.  
This page is **read‑only**.

---

### 3. **Student Roster Page**
Split into two clean sections:

#### A. Add Student
- Email input  
- Add Student button  
- Success toast  

#### B. Student List
- Table or list  
- Search bar  
- Optional remove student action  

Keep layout simple and modern.

---

### 4. **Assessments Page**
This page must contain **two tabs**:

#### Tab 1: Create Assessment
Move the existing form here:
- Subject  
- Chapter  
- Exam Title  
- Difficulty  
- Question Type (MCQ / Numerical / Both)  
- Number of Questions  
- Time Limit  
- Create Assessment button  

After creation, show a success message and a link/button:  
**“Proceed to Assign Assessment”**

#### Tab 2: Assign Assessment
Move assignment workflow here:
- Select Assessment  
- Select Students (multi‑select)  
- Assign Exam button  
- Success toast  

Tabs must clearly separate creation vs assignment.

---

### 5. **Question Bank Page**
Move the question list here and add filters:

Filters required:
- Subject  
- Chapter  
- Topic  
- Difficulty  
- Question Type  
- Status (Validated / Generated / Rejected)

Display questions using:
- Paginated list  
- Collapsible cards  
- Or a clean table  

Add a modal or expandable section for question details.

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
- Reuse existing backend logic and functions.  
- Do not break existing API calls or database operations.  
- Only reorganize UI and UX.  
- Keep code modular and readable.  
- Create new files if needed (e.g., `teacher_analytics.py`, `teacher_roster.py`, etc.).  
- Ensure navigation works smoothly from the sidebar and between sub‑pages.  
- Ensure all new pages inherit the existing theme and styling conventions.

---

## 🎯 Final Deliverable
Rewrite the Teacher module so that:
- The landing page is clean and modern  
- Each workflow has its own dedicated sub‑page  
- No clutter  
- No long scrolling  
- UX feels like a professional EdTech platform  
- All pages remain fully aligned with the existing GitHub Dark theme and typography  

Make all necessary code changes across the Streamlit app to implement this redesign.
