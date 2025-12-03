# [IE104.Q11.CNVN] - Tourist Guide Website Project

## 🎓 Team Introduction

- **University**: University of Information Technology, VNU-HCM
- **Faculty**: Information Technology
- **Supervisor**: MSc. Vo Tan Khoa
- **Student Group**: Group 3

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

👉 [Watch the full code demo video here](https://www.youtube.com/watch?v=z6BVyc0Qvzk)

### Live Demo

👉 [View live demo here](https://gohcmc-ie104.onrender.com/)

### Introduction

This isn’t your average travel app. It blends real-world usefulness with intelligent automation, sentiment-aware recommendations, and natural conversation interfaces. The goal: a truly smart tourist assistant that feels personal, responsive, and actually helpful.

### System Architecture

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Backend**: Python 3.11, Django Framework
- **Database**: SQLite (default Django ORM)
- **AI & Chatbot**: Google Dialogflow
- **Data Processing**: Pandas, CSV handling
- **Weather API**: Integrated external weather service
- **Containerization**: Docker, Docker Compose
- **Version Control**: Git, GitHub
- **Development Environment**: Visual Studio Code with Dev Containers

---

## 📁 Project Structure

```

IE104_GoHCMC/
├── manage.py 
├── importing.py
├── Dockerfile
├── docker-compose.yml
├── Procfile
├── runtime.txt
├── GoHCMC/
│ ├── __init__.py
│ ├── asgi.py
│ ├── settings.py
│ ├── urls.py
│ └── wsgi.py
├── data/
│   ├── clean/
│   ├── crawl/
│   ├── ETL/
│   └── raw/
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

- **User Authentication**: Secure registration, login, and password reset via email with comprehensive validation
- **Responsive Design**: Mobile-friendly interface with light/dark theme toggle optimized for all devices
- **Location Exploration**: Browse locations with detailed information, ratings, and filtering by type, rating, opening time, and search queries
- **Interactive Comments**: Post comments with ratings on locations, featuring AI-powered sentiment analysis and automated bot replies

### 🚀 Advanced

**🗺 Smart Trip Planner**
- Create multi-stop trips with custom start and end points, mandatory waypoints, and precedence constraints
- Optimized route calculation using a simplified Hamiltonian Path algorithm for shortest paths
- Trip history saved with distance and duration estimates using real-time distance matrix API

**🤖 AI-Powered Chatbot**
- Integrated Google Dialogflow for natural language conversation and trip planning
- Voice/text commands to add/remove favorites, set trip start/end points, and generate optimized itineraries
- Session-based temporary trip carts for unauthenticated users

**📊 Sentiment Analysis**
- Machine learning model (SVM with TF-IDF) analyzes user comments to generate automatic ratings and responses
- Enhances user experience with sentiment-aware recommendations and personalized bot interactions

**🌤️ Weather Integration**
- Real-time 3-day weather forecasts for locations using WeatherAPI
- Interactive charts showing temperature and precipitation with theme-aware visualization
- Helps users plan trips based on current and forecasted weather conditions

**💬 Interactive Features**
- Favourite locations management with heart-based toggling
- Hierarchical comments system with replies and flagging capabilities
- Email notifications and secure password management

**📈 Data Processing & ETL**
- Automated data pipeline for importing attractions, restaurants, and hotels from raw CSV/JSON sources
- TF-IDF based tag generation for location categorization and search enhancement
- Sentiment analysis model training using SVM for comment classification

---

## 📋 Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose
- Visual Studio Code with Dev Containers extension (for local development)

---

## 🚀 Run the App Locally

```bash
# Clone the repo
git clone https://github.com/howardVoxcan/IE104_GoHCMC.git
cd IE104_GoHCMC

# Environment Setup (skip if already in dev container)
Install Docker Desktop and open the app
In Visual Studio Code: Ctrl + Shift + P --> DevContainer: Rebuild & reopen

# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py migrate

# Collect static files (optional, for production)
python manage.py collectstatic --noinput

# Run project
python manage.py runserver
Website runs at: http://localhost:5000
```

---

## 🤝 Contribute
1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request
