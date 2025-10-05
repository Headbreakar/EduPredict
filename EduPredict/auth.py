from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from educationmodel.models import Signup, Feedback

import pandas as pd
import json
import os
import joblib
import csv  # <-- YOU FORGOT THIS ONE, BRO

from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LinearRegression


uploaded_df = None  # temporary global storage

def adminDashboard(request):
    # If some rows have null usertype, exclude them to avoid noise
    total_students = Signup.objects.filter(usertype__iexact='student').count()
    total_teachers = Signup.objects.filter(usertype__iexact='teacher').count()
    return render(request, "admin_dashboard.html", {
        "total_students": total_students,
        "total_teachers": total_teachers,
    })

def uploadExcel(request):
    global uploaded_df
    if request.method == 'POST' and request.FILES['file']:
        data_file = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(data_file.name, data_file)
        file_path = fs.path(filename)

        # Check extension
        if filename.endswith(".csv"):
            uploaded_df = pd.read_csv(file_path)
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            uploaded_df = pd.read_excel(file_path)
        else:
            messages.error(request, "Only CSV and Excel files are supported.")
            return redirect("admin-dashboard")

        # Handle missing values (numeric → mean, categorical → mode)
        for col in uploaded_df.columns:
            if uploaded_df[col].dtype in ['int64', 'float64']:
                uploaded_df[col] = uploaded_df[col].fillna(uploaded_df[col].mean())
            else:
                uploaded_df[col] = uploaded_df[col].fillna(uploaded_df[col].mode()[0])

        # Normalize numeric columns
        numeric_cols = uploaded_df.select_dtypes(include=['int64', 'float64']).columns
        uploaded_df[numeric_cols] = (uploaded_df[numeric_cols] - uploaded_df[numeric_cols].min()) / (uploaded_df[numeric_cols].max() - uploaded_df[numeric_cols].min())

        # Column selection
        columns = uploaded_df.columns.tolist()
        return render(request, "select_column.html", {"columns": columns})

    return redirect("admin-dashboard")


def selectColumn(request):
    if request.method == "POST":
        features = request.POST.getlist('features')   # multiple selection
        target = request.POST.get('target')           # single selection

        if not features or not target:
            messages.error(request, "Select at least one feature and one target.")
            return redirect("admin-dashboard")

        request.session['features'] = features
        request.session['target'] = target
        return redirect("process-data")
    return redirect("admin-dashboard")



def processData(request):
    global uploaded_df
    features = request.session.get('features')
    target = request.session.get('target')

    if uploaded_df is not None and features and target:
        # Handle missing values
        for col in uploaded_df.columns:
            if uploaded_df[col].dtype in ['int64', 'float64']:
                uploaded_df[col] = uploaded_df[col].fillna(uploaded_df[col].mean())
            else:
                uploaded_df[col] = uploaded_df[col].fillna(uploaded_df[col].mode()[0])

        # Normalize
        numeric_cols = uploaded_df.select_dtypes(include=['int64','float64']).columns
        uploaded_df[numeric_cols] = (uploaded_df[numeric_cols] - uploaded_df[numeric_cols].min()) / (
            uploaded_df[numeric_cols].max() - uploaded_df[numeric_cols].min()
        )

        # Encode categorical
        cat_cols = uploaded_df.select_dtypes(include=['object']).columns
        le = LabelEncoder()
        for col in cat_cols:
            uploaded_df[col] = le.fit_transform(uploaded_df[col].astype(str))

        # Final X, y
        X = uploaded_df[features]
        y = uploaded_df[target]

        # Train linear regression model
        model = LinearRegression()
        model.fit(X, y)

        # Save model for future predictions
        os.makedirs("models", exist_ok=True)
        model_path = os.path.join("models", "latest_model.pkl")
        joblib.dump({
            "model": model,
            "features": features,
            "target": target
        }, model_path)

        # Create output info
        table_classes = "min-w-full border border-gray-300 rounded-lg text-sm"
        tbody_classes = "divide-y divide-gray-200"

        df_info = {
            "rows": uploaded_df.shape[0],
            "cols": uploaded_df.shape[1],
            "features": features,
            "target": target,
            "sample_X": X.head(10).to_html(classes=f"dataframe {table_classes}", border=0, index=False)
                          .replace("<tbody>", f"<tbody class='{tbody_classes}'>"),
            "sample_y": y.head(10).to_frame().to_html(classes=f"dataframe {table_classes}", border=0, index=False)
                          .replace("<tbody>", f"<tbody class='{tbody_classes}'>"),
            "correlations": uploaded_df.corr(numeric_only=True).to_html(classes=f"dataframe {table_classes}", border=0)
                          .replace("<tbody>", f"<tbody class='{tbody_classes}'>"),
            "y_values": json.dumps(y.head(20).tolist()),
            "corr_values": json.dumps(uploaded_df.corr(numeric_only=True)[target].dropna().to_dict()),
            "model_saved": True
        }

        return render(request, "process_result.html", {"df_info": df_info})

    messages.error(request, "No data to process")
    return redirect("admin-dashboard")




# Signup View
def signupPageinserted(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        password = request.POST['password']
        usertype = request.POST['usertype']   # new field from form

        if Signup.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
        else:
            user = Signup.objects.create(
                name=name, 
                email=email, 
                password=password, 
                usertype=usertype
            )
            user.save()
            messages.success(request, "Account created successfully!")
            return render(request, 'login.html')



def loginpage(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        checkdata = Signup.objects.filter(email=email, password=password).first()

        if checkdata:
            request.session["getname"] = checkdata.name
            request.session["getid"] = checkdata.id
            request.session["usertype"] = checkdata.usertype

            # Redirect based on user type
            if checkdata.usertype == 'admin':
                return render(request, 'admin_dashboard.html')
            elif checkdata.usertype == 'teacher':
                return render(request, 'teacher_dashboard.html')
            else:
                return render(request, 'student_dashboard.html')
        else:
            messages.error(request, 'Invalid Credential')
            return render(request, 'login.html')
	


# Home View
def homePage(request) : 
    return render(request , 'home.html')

# About View
def aboutPage(request) : 
    return render(request , 'about.html')
def loginView(request) : 
    return render(request , 'login.html')
# Contact View
def contactPage(request) : 
    return render(request , 'contact.html')

# Forgot Password View
def forgotPasswordPage(request) : 
    return render(request , 'forgot-password.html')


def SignupPage(request) : 
    return render(request , 'signup.html')


def logout(request) : 
    request.session.flush()
    return render(request , 'login.html')


def teacherDashboard(request): 
    # If some rows have null usertype, exclude them to avoid noise
    total_students = Signup.objects.filter(usertype__iexact='student').count()
    return render(request, "teacher_dashboard.html", {
        "total_students": total_students
    })

def studentDashboard(request):
    return render(request, 'student_dashboard.html')



def feedbackinsert(request) : 
    if request.method == 'POST' :
        name = request.POST["name"]
        email = request.POST["email"]
        subject = request.POST["subject"]
        message = request.POST["message"]
        userid = request.session.get('getid')
    if userid : 
        feedbackdata = Signup.objects.get(id=userid)
        feedbackdatainsert = Feedback.objects.create(name=name,email=email,message = message,fkuser =feedbackdata)
        feedbackdatainsert.save()
        return render(request, 'contact.html')
    else :
        messages.error(request,'Login to give feedback')
        return render(request, 'contact.html')    



# -------- Students CRUD --------
def add_student(request):
    if request.method == "POST":
        Signup.objects.create(
            name=request.POST['name'],
            email=request.POST['email'],
            password=request.POST['password'],
            usertype="student",
            class_name=request.POST['class_name'],
            roll_no=request.POST['roll_no']
        )
        messages.success(request, "Student added successfully!")
        return redirect("students-list")
    return render(request, "add_student.html")

def students_list(request):
    students = Signup.objects.filter(usertype="student")
    return render(request, "students_list.html", {"students": students})

def edit_student(request, pk):
    student = Signup.objects.get(id=pk, usertype="student")
    if request.method == "POST":
        student.name = request.POST['name']
        student.email = request.POST['email']
        student.password = request.POST['password']
        student.class_name = request.POST['class_name']
        student.roll_no = request.POST['roll_no']
        student.save()
        messages.success(request, "Student updated successfully!")
        return redirect("students-list")
    return render(request, "edit_student.html", {"student": student})

def delete_student(request, pk):
    student = Signup.objects.get(id=pk, usertype="student")
    student.delete()
    messages.success(request, "Student deleted successfully!")
    return redirect("students-list")


# -------- Teachers CRUD --------
def add_teacher(request):
    if request.method == "POST":
        Signup.objects.create(
            name=request.POST['name'],
            email=request.POST['email'],
            password=request.POST['password'],
            usertype="teacher",
            subject=request.POST['subject'],
            department=request.POST['department']
        )
        messages.success(request, "Teacher added successfully!")
        return redirect("teachers-list")
    return render(request, "add_teacher.html")

def teachers_list(request):
    teachers = Signup.objects.filter(usertype="teacher")
    return render(request, "teachers_list.html", {"teachers": teachers})

def edit_teacher(request, pk):
    teacher = Signup.objects.get(id=pk, usertype="teacher")
    if request.method == "POST":
        teacher.name = request.POST['name']
        teacher.email = request.POST['email']
        teacher.password = request.POST['password']
        teacher.subject = request.POST['subject']
        teacher.department = request.POST['department']
        teacher.save()
        messages.success(request, "Teacher updated successfully!")
        return redirect("teachers-list")
    return render(request, "edit_teacher.html", {"teacher": teacher})

def delete_teacher(request, pk):
    teacher = Signup.objects.get(id=pk, usertype="teacher")
    teacher.delete()
    messages.success(request, "Teacher deleted successfully!")
    return redirect("teachers-list")



def studentInput(request):
    """
    Display a form for students to input their own details (like study hours, attendance, etc.)
    Once submitted, the data will be passed through the trained model to generate a predicted score.
    """
    if request.method == "POST":
        # Load the latest trained model
        model_path = "models/latest_model.pkl"
        if not os.path.exists(model_path):
            messages.error(request, "No trained model found. Please ask your teacher to upload a dataset first.")
            return redirect("student-dashboard")

        model_data = joblib.load(model_path)
        model = model_data["model"]
        features = model_data["features"]

        # Build input row from form fields
        student_data = []
        for f in features:
            value = float(request.POST.get(f, 0))
            student_data.append(value)

        # Make prediction
        prediction = model.predict([student_data])[0]

        # Save result in session for later download
        request.session["student_prediction"] = prediction
        request.session["can_download"] = True
        messages.success(request, f"Your predicted performance score is {round(prediction, 2)}!")
        return redirect("student-dashboard")

    # If GET request, render the form dynamically based on model features
    model_path = "models/latest_model.pkl"
    if os.path.exists(model_path):
        model_data = joblib.load(model_path)
        features = model_data["features"]
        return render(request, "student_input.html", {"features": features})
    else:
        messages.error(request, "No model available yet.")
        return redirect("student-dashboard")


def downloadPrediction(request):
    prediction = request.session.get("student_prediction")
    student_inputs = request.session.get("student_inputs", {})  # all filled fields
    if prediction is None:
        messages.error(request, "No prediction found. Please fill your info first.")
        return redirect("student-dashboard")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="Predicted_Performance_Report.csv"'
    writer = csv.writer(response)

    # Header
    writer.writerow(["===================== EDU PREDICT REPORT ====================="])
    writer.writerow([])

    # Student info
    writer.writerow(["Student Name", request.session.get("getname", "Unknown Student")])
    writer.writerow([])

    # Input section header
    writer.writerow(["--- Submitted Details ---"])
    writer.writerow(["Feature", "Value"])
    for key, value in student_inputs.items():
        writer.writerow([key.replace("_", " ").title(), value])

    writer.writerow([])
    writer.writerow(["--- Prediction ---"])
    writer.writerow(["Predicted Exam Score", round(prediction, 2)])
    writer.writerow([])

    writer.writerow(["=============================================================="])
    writer.writerow(["Generated by EduPredict AI Model"])
    return response

    """
    Allows student to download their predicted performance as a CSV file.
    Only enabled after they submit their input form.
    """
    prediction = request.session.get("student_prediction")
    if prediction is None:
        messages.error(request, "No prediction found. Please fill your info first.")
        return redirect("student-dashboard")

    # Create a simple CSV response
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="predicted_performance.csv"'
    writer = csv.writer(response)
    writer.writerow(["Student Name", "Predicted Score"])
    writer.writerow([request.session.get("getname", "Unknown Student"), round(prediction, 2)])
    return response

def create_default_site_users():
    default_users = [
        {
            "name": "System Admin",
            "email": "admin@edupredict.com",
            "password": "admin123",
            "usertype": "admin"
        },
        {
            "name": "John Teacher",
            "email": "teacher@edupredict.com",
            "password": "teach123",
            "usertype": "teacher"
        },
        {
            "name": "Alice Student",
            "email": "student@edupredict.com",
            "password": "study123",
            "usertype": "student"
        },
    ]

    for user in default_users:
        if not Signup.objects.filter(email=user["email"]).exists():
            Signup.objects.create(**user)
            print(f"Created default {user['usertype']} account: {user['email']}")

# Safely create defaults when the app starts
try:
    create_default_site_users()
except Exception as e:
    print("Default user setup skipped:", e)