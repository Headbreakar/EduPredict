# EduPredict

EduPredict is a Django-based machine learning web application that predicts student performance using educational datasets. Admins upload datasets, teachers manage users, and students get personalized performance predictions.

---

## Overview
EduPredict leverages data analytics and machine learning to improve academic performance prediction.  
The system allows:
- **Admins** to upload educational datasets (CSV/Excel) and train regression models.  
- **Teachers** to manage students and monitor datasets.  
- **Students** to input their details and receive a predicted exam score with downloadable reports.

---

## Tech Stack
- **Backend:** Python, Django  
- **Frontend:** HTML, Tailwind CSS  
- **Database:** SQLite (for MVP)  
- **Machine Learning:** Scikit-Learn, Pandas, Joblib  

---

## Setup
```bash
git clone https://github.com/Headbreakar/EduPredict
cd EduPredict
python -m venv venv
venv\Scripts\activate   # For Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Then open:  
➡️ `http://127.0.0.1:8000/`

---

## Default Users
| Role | Email | Password |
|------|--------|-----------|
| Admin | admin@edupredict.com | admin123 |
| Teacher | teacher@edupredict.com | teacher123 |
| Student | student@edupredict.com | student123 |

---

## Key Routes
| Route | Description |
|-------|-------------|
| `/` | Login Page |
| `/signup/` | Register New User |
| `/admin-dashboard/` | Admin Panel |
| `/upload-excel/` | Upload Dataset |
| `/process-data/` | Train Model |
| `/student-dashboard/` | Student Panel |
| `/student/input/` | Fill Student Info |
| `/student/download/` | Download Report |
| `/logout/` | End Session |

---

## Code Structure
```
EduPredict/
├── EduPredict/
│   ├── settings.py
│   ├── urls.py
│   └── auth.py          # Core logic (auth, ML, CRUD, predictions)
├── educationmodel/
│   ├── models.py        # Signup, Feedback models
│   └── migrations/
├── templates/
│   ├── *.html           # Dashboards, forms, pages
├── models/
│   └── latest_model.pkl # Saved trained model
└── static/
    └── tailwind/        # Styling assets
```

---

## Model Training Workflow
1. **Admin Uploads Data**  
   Upload CSV/Excel → Clean → Normalize → Encode categorical columns  
2. **Model Training**  
   Linear Regression → Features and Target stored → Model saved via `joblib`  
3. **Prediction Phase**  
   Students fill inputs → Model predicts `Exam_Score` → Result displayed + downloadable CSV  

---

## Output
- Predicted performance score displayed to the student.  
- Styled CSV report showing all input features + predicted score.  
- Correlation visualization shown in admin dashboard (tabular + chart).  

---

## Planned Enhancements
- Migrate data handling to **HDFS** for large-scale ingestion.  
- Introduce **real-time prediction pipelines** using Kafka/Spark.  
- Build **Tableau/Power BI dashboards** for visual insights.  
- Integrate **automated feedback learning loops** for adaptive retraining.  

---

## Team
| Name | Role | Responsibilities |
|------|------|------------------|
| **Nimra Asif** | Student1447550 | Authentication, correlation visualization, backend data handling |
| **Mayur Parmar** | Student1418422 | Frontend design, testing workflows, report review |
| **Zohra Akbar** | Student1445801 | Feedback handling, model testing |
| **Prem Kumar** | Student1444433 | Dataset upload, training pipeline, prediction logic, documentation |

---

## License
MIT License – feel free to modify or extend for educational use.
