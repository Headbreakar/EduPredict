from django.contrib import admin
from django.urls import path
from EduPredict import auth

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth
    path('', auth.loginView, name="login"),
    path('signup/', auth.SignupPage, name='signup'),
    path('signupinserted/', auth.signupPageinserted),
    path('loginresult/', auth.loginpage),
    path('logout/', auth.logout, name='logout'),

    path('feedbackinserted/', auth.feedbackinsert),
    path('forgot-password/', auth.forgotPasswordPage, name='forgot-password'),

    # Pages 
    path('home/', auth.homePage, name='home'),
    path('about/', auth.aboutPage, name='about'),
    path('contact/', auth.contactPage, name='contact'),

    # Dashboards
    path('admin-dashboard/', auth.adminDashboard, name='admin-dashboard'),
    path('teacher-dashboard/', auth.teacherDashboard, name='teacher-dashboard'),
    path('student-dashboard/', auth.studentDashboard, name='student-dashboard'),

    # Data Processing
    path('upload-excel/', auth.uploadExcel, name='upload-excel'),
    path('select-column/', auth.selectColumn, name='select-column'),
    path('process-data/', auth.processData, name='process-data'),

    # Students CRUD
    path("students/add/", auth.add_student, name="add-student"),
    path("students/", auth.students_list, name="students-list"),
    path("students/edit/<int:pk>/", auth.edit_student, name="edit-student"),
    path("students/delete/<int:pk>/", auth.delete_student, name="delete-student"),

    # Teachers CRUD
    path("teachers/add/", auth.add_teacher, name="add-teacher"),
    path("teachers/", auth.teachers_list, name="teachers-list"),
    path("teachers/edit/<int:pk>/", auth.edit_teacher, name="edit-teacher"),
    path("teachers/delete/<int:pk>/", auth.delete_teacher, name="delete-teacher"),

    # NEW — Student Prediction Routes
    path("student/input/", auth.studentInput, name="student-input"),
    path("student/download/", auth.downloadPrediction, name="download-prediction"),
]
