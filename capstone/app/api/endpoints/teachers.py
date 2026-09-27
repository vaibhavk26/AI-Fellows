from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_teacher
from app.api.dependencies.database import get_db
from app.api.schemas.auth import UserResponse
from app.api.schemas.teacher import AddStudentRequest
from app.db.models.extensions import TeacherStudent
from app.db.models.user import User

router = APIRouter(prefix="/api/v1/teachers/me", tags=["teachers"])


@router.get("/students")
def list_students(current_user: UserResponse = Depends(get_current_teacher), db: Session = Depends(get_db)) -> dict:
    students = db.query(User).join(TeacherStudent, TeacherStudent.student_id == User.id).filter(
        TeacherStudent.teacher_id == current_user.id
    ).order_by(User.full_name, User.email).all()
    return {"data": [{"id": student.id, "full_name": student.full_name, "email": student.email} for student in students], "meta": None}


@router.post("/students", status_code=status.HTTP_201_CREATED)
def add_student(request: AddStudentRequest, response: Response, current_user: UserResponse = Depends(get_current_teacher), db: Session = Depends(get_db)) -> dict:
    student = db.query(User).filter(func.lower(User.email) == request.email.lower(), User.role == "student").one_or_none()
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registered student was not found")
    membership = db.query(TeacherStudent).filter_by(teacher_id=current_user.id, student_id=student.id).one_or_none()
    if membership is None:
        db.add(TeacherStudent(teacher_id=current_user.id, student_id=student.id))
        db.commit()
    else:
        response.status_code = status.HTTP_200_OK
    return {"data": {"id": student.id, "full_name": student.full_name, "email": student.email}, "meta": None}