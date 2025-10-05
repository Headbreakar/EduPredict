from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from educationmodel.models import Signup, Feedback

import pandas as pd
import json
import os
import joblib
import csv

from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LinearRegression


uploaded_df = None  # Temporary global storage for uploaded data


# -------------------- DASHBOARDS --------------------

def adminDashboard(request):
    total_students = Signup.objects.filter(usertype__iexact='student').count()
    total_teachers = Signup.objects.filter(usertype__iexact='teacher').count()
    return render(request, "admin_dashboard.html", {
        "total_students": total_students,
        "total_teachers": total_teachers,
    })


def teacherDashboard(request):
    total_students = Signup.objects.filter(usertype__iexact='student').count()
    return render(request, "teacher_dashboard.html", {"total_students": total_students})


def studentDashboard(request):
    return render(request, "student_dashboard.html")


# -------------------- DATA UPLOAD & MODEL TRAINING --------------------

def uploadExcel(request):
    global uploaded_df
    if request.method == 'POST' and request.FILES['file']:
        data_file = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(data_file.name, data_file)
        file_path = fs.path(filename)

        # Read data
        if filename.endswith(".csv"):
            uploaded_df = pd.read_csv(file_path)
        elif filename.endswith((".xlsx", ".xls")):
            uploaded_df = pd.read_excel(file_path)
        else:
            messages.error(request, "Only CSV and Excel files are supported.")
            return redirect("admin-dashboard")

        # Handle missing values
        for col in uploaded_df.columns:
            if uploaded_df[col].dtype in ['int64', 'float64']:
                uploaded_df[col] = uploaded_df[col].fillna(uploaded_df[col].mean())
            else:
                uploaded_df[col] = uploaded_df[col].fillna(uploaded_df[col].mode()[0])

        # Normalize numeric columns
        numeric_cols = uploaded_df.select_dtypes(include=['int64', 'float64']).columns
        uploaded_df[numeric_cols] = (uploaded_df[numeric_cols] - uploaded_df[numeric_cols].min()) / (
            uploaded_df[numeric_cols].max() - uploaded_df[numeric_cols].min()
        )

        # Send column names for selection
        columns = uploaded_df.columns.tolist()
        return render(request, "select_column.html", {"columns": columns})

    return redirect("admin-dashboard")


def selectColumn(request):
    if request.method == "POST":
        features = request.POST.getlist('features')
        target = request.POST.get('target')

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
        numeric_cols = uploaded_df.select_dtypes(include=['int64', 'float64']).columns
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

        # Save model
        os.makedirs("models", exist_ok=True)
        model_path = os.path.join("models", "latest_model.pkl")
        joblib.dump({
            "model": model,
            "features": features,
            "target": target
        }, model_path)

        # Prepare info for dashboard
        df_info = {
            "rows": uploaded_df.shape[0],
            "cols": uploaded_df.shape[1],
            "features": features,
            "target": target,
            "sample_X": X.head(10).to_html(border=0, index=False),
            "sample_y": y.head(10).to_frame().to_html(border=0, index=False),
            "correlations": uploaded_df.corr(numeric_only=True).to_html(border=0),
            "y_values": json.dumps(y.head(20).tolist()),
            "corr_values": json.dumps(uploaded_df.corr(numeric_only=True)[target].dropna().to_dict()),
            "model_saved": True
        }

        return render(request, "process_result.html", {"df_info": df_info})

    messages.error(request, "No data to process")
    return redirect("admin-dashboard")


# -------------------- STUDENT PERFORMANCE PREDICTION --------------------

def studentInput(request):
    features = [
        "Hours_Studied", "Attendance", "Parental_Involvement", "Access_to_Resources",
        "Extracurricular_Activities", "Sleep_Hours", "Previous_Scores", "Motivation_Level",
        "Internet_Access", "Tutoring_Sessions", "Family_Income", "Teacher_Quality",
        "School_Type", "Peer_Influence", "Physical_Activity", "Learning_Disabilities",
        "Parental_Education_Level", "Distance_from_Home", "Gender"
    ]

    dropdown_low_med_high = [
        "Parental_Involvement", "Access_to_Resources", "Motivation_Level",
        "Family_Income", "Teacher_Quality", "School_Type",
        "Peer_Influence", "Parental_Education_Level"
    ]

    dropdown_yes_no = [
        "Internet_Access", "Extracurricular_Activities", "Learning_Disabilities"
    ]

    if request.method == "POST":
        model_path = "models/latest_model.pkl"
        if not os.path.exists(model_path):
            messages.error(request, "No trained model found. Please ask your teacher to upload the dataset first.")
            return redirect("student-dashboard")

        model_data = joblib.load(model_path)
        model = model_data["model"]

        student_data = {}
        for f in features:
            val = request.POST.get(f, "")
            student_data[f] = val

        # convert categorical inputs to simple numeric representations
        encoded_data = []
        for val in student_data.values():
            if val.lower() in ["yes", "high", "positive", "public", "male"]:
                encoded_data.append(1)
            elif val.lower() in ["no", "low", "negative", "private", "female"]:
                encoded_data.append(0)
            else:
                try:
                    encoded_data.append(float(val))
                except:
                    encoded_data.append(0)

        prediction = model.predict([encoded_data])[0]

        request.session["student_inputs"] = student_data
        request.session["student_prediction"] = prediction
        request.session["can_download"] = True
        messages.success(request, f"Your predicted exam score is {round(prediction, 2)}!")
        return redirect("student-dashboard")

    return render(request, "student_input.html", {
        "features": features,
        "dropdown_low_med_high": dropdown_low_med_high,
        "dropdown_yes_no": dropdown_yes_no
    })


def downloadPrediction(request):
    model_path = os.path.join("models", "latest_model.pkl")
    if not os.path.exists(model_path):
        messages.error(request, "No trained model available.")
        return redirect("student-dashboard")

    if not request.session.get("can_download"):
        messages.error(request, "Please submit your details first.")
        return redirect("student-dashboard")

    model_data = joblib.load(model_path)
    model = model_data["model"]
    features = model_data["features"]
    target = model_data["target"]
    student_inputs = request.session.get("student_inputs")

    if not student_inputs:
        messages.error(request, "Missing input data.")
        return redirect("student-dashboard")

    X_new = pd.DataFrame([student_inputs])
    predicted = model.predict(X_new)[0]

    # Build CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename=Predicted_Performance.csv'
    writer = csv.writer(response)
    writer.writerow(["Feature", "Value"])
    for k, v in student_inputs.items():
        writer.writerow([k, v])
    writer.writerow(["Predicted " + target, round(predicted, 2)])

    return response
