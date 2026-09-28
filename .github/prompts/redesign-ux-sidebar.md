I want you to refactor the Streamlit sidebar navigation to implement **Persona‑Aware Sidebar**, ensuring that Students and Teachers only see pages relevant to their persona.

Do **not** modify backend logic, database operations, or API calls.  
Do **not** break existing workflows.  
Only reorganize the UI and navigation structure.

**IMPORTANT:**  
Preserve the existing **GitHub Dark theme**, color palette, spacing, and typography used throughout the application.  
All redesigned navigation must visually align with the current global theme.

---

## 🎯 Goal
Implement a **persona‑aware sidebar** that dynamically shows different navigation items depending on whether the logged‑in user is a **Student** or **Teacher**.

The sidebar must automatically adapt based on the authenticated user’s role.

---

## 👨‍🎓 Student Sidebar (Only for Student persona)
Show ONLY these pages:

- Dashboard  
- Exam  
- Results  

Optional (if already implemented):
- Profile  
- Settings  
- Logout  

Students must NOT see:
- Teacher  
- Generate  
- Teacher Analytics  
- Roster  
- Assessments  
- Question Bank  

---

## 👨‍🏫 Teacher Sidebar (Only for Teacher persona)
Show ONLY these pages:

- Teacher Hub (Landing page)  
- Analytics  
- Roster  
- Assessments  
- Question Bank  
- Generate Questions  

Optional:
- Profile  
- Settings  
- Logout  

Teachers must NOT see:
- Dashboard  
- Exam  
- Results  

---

## 🔐 Authentication Sidebar (Before Login)
Before login, show ONLY:

- Sign In  
- Sign Up  

After login, these must disappear.

---

## 🛠️ Implementation Requirements
- Use the existing authentication mechanism to detect persona (Student vs Teacher).  
- Use conditional logic to render different sidebar items based on persona.  
- Ensure navigation works with the existing multi‑page Streamlit structure.  
- Do not break any backend functions or database interactions.  
- Reuse existing page files; only reorganize how they appear in the sidebar.  
- Ensure the new sidebar integrates seamlessly with the redesigned Teacher module.  
- Maintain the GitHub Dark theme and typography across all new sidebar elements.

---

## 🎨 UX Requirements
- Sidebar must be clean, minimal, and aligned with modern EdTech UX.  
- No clutter.  
- No irrelevant pages shown to the user.  
- Sidebar items should be grouped logically and consistently.  
- Maintain spacing, padding, and visual hierarchy consistent with the rest of the app.

---

## 🎯 Final Deliverable
Refactor the sidebar so that:
- Students see only Student pages  
- Teachers see only Teacher pages  
- Authentication pages appear only before login  
- All styling remains consistent with the GitHub Dark theme  
- No backend logic is broken  
- Navigation remains smooth and intuitive  

Make all necessary UI changes to implement this persona‑aware sidebar without altering backend functionality.
