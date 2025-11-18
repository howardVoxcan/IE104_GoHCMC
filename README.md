# [IE104.Q11.CNVN] - Tourist Guide Website Project

## 🎓 Team Introduction

University: University of Information Technology, VNU-HCM
Faculty: Information Technology
Supervisor: MSc. Vo Tan Khoa
Student Group: Group 3

---

## 👥 Members

| No. | Name               | Student ID | Role         |
| --- | ------------------ | ---------- | ------------ |
| 1   | Võ Quang Nhật Hoàng| 22520482   | Group Leader |
| 2   | Nguyễn Thanh Trí   | 23521645   | Member       |
| 3   | Trần Minh Hoài Tâm | 23521394   | Member       |
| 4   | Lê Thị Thùy Trang  | 23521627   | Member       |
| 5   | Nguyễn Minh Tuấn   | 23521720   | Member       |

---

## 🛠️ Technologies Used

### Full Code Demo Video

👉 [Watch the full code demo video here]_

### Introduction

This isn’t your average travel app. It blends real-world usefulness with intelligent automation, sentiment-aware recommendations, and natural conversation interfaces. The goal: a truly smart tourist assistant that feels personal, responsive, and actually helpful.

### System Architecture

**Frontend**: HTML/CSS, JavaScript
**Backend**: Python Django
**Container**: Docker

---

## 📁 Cấu trúc thư mục

```

IE104_GoHCMC/
├── manage.py 
├── importing.py
├── GoHCMC/
│ ├── _init_.py
│ ├── asgi.py
│ ├── settings.py
│ ├── urls.py
│ └── wsgi.py
├── data/
├── dialogflow/
├── favourite/
├── location/
├── register/
├── static/
│ ├── css/
│ ├── data/
│ └── img/
├── staticfiles/
├── templates/
│ ├── components/
│ └── page/
│   ├── favourite/
│   ├── home/
│   ├── locations/
│   ├── my_trip/
│   ├── weather/
│   └── layout.html
├── trip/
├── weather/
├── data.csv
├── data_with_tags.csv
├── render.yaml
└── requirements.txt

```


---

## ✨ Key Features

### ✅ Basic

Clean, mobile-friendly homepage and UI
Explore locations with full detail view and live 3-day weather forecast
Save favorite locations and manage personalized trip lists

### 🚀 Advanced

**🗺 Smart Trip Planner**
Plan multi-stop trips with custom start and end points
Route optimized via a simplified Hamiltonian Path algorithm
Trip paths are saved to user history

---

## 🚀 Run the App Locally

```
# Clone the repo
git clone https://github.com/howardVoxcan/IE104_GoHCMC.git
cd IE104_GoHCMC

# Enviroment
Install Docker Desktop
Open app
In Visual Studio Code: Ctrl + Shift + P --> DevContainer: Rebuid & reopen 

# Install dependencies
pip install -r requirements.txt

# Run project
python manage.py runserver
Website run in: http://localhost:5000
```

---

## 🤝 Đóng góp
1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request
