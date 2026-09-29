# 📊 Customer Churn Prediction

A machine learning-based web application that predicts customer churn using a **Random Forest Classifier** and provides interactive customer analytics through **Streamlit**.

The application combines machine learning, customer analytics, visualization, and an interactive web interface to help identify customers who may be at risk of leaving a service.

## 🚀 Live Demo

🌐 **Live Application:**  
https://customerchurnprediction-mrcximrpff4u9wy32yvufn.streamlit.app/

---

## 📌 Project Overview

Customer churn prediction helps businesses identify customers who are likely to leave their service.

This project uses customer data and a trained **Random Forest Classifier** to predict whether a customer is likely to churn.

The Streamlit application provides an interactive interface for:

- Customer analysis
- Customer segmentation
- Churn prediction
- Business intelligence
- Model evaluation
- Prediction history
- Customer analytics
- Contract-wise churn analysis

---

## ✨ Features

- 🔐 **Admin Login**
- 📊 **Interactive Dashboard**
- 👤 **Customer Profile**
- 🌐 **Customer 360**
- 🎯 **Customer Segmentation**
- 📈 **Business Intelligence**
- 🤖 **Customer Churn Prediction**
- 🧪 **Model Evaluation**
- 📋 **Prediction History**
- 📊 **Customer Analytics**
- 📉 **Contract-wise Churn Analysis**
- 🌲 **Random Forest Machine Learning Model**

---

## 🤖 Machine Learning

### Model Used

**Random Forest Classifier**

The trained model is stored in:

```text
data/random_forest_model.pkl
```

Supporting model files:

```text
data/feature_names.pkl
data/model_columns.pkl
```

The application loads these trained model files to generate customer churn predictions.

---

## 📊 Model Performance

| Metric | Score |
|---|---:|
| Accuracy | **75.20%** |
| ROC-AUC | **83.79%** |
| F1 Score | **62.99%** |
| Model | **Random Forest** |

These metrics represent the performance values used in the deployed application.

---

## 🛠️ Technologies Used

### Programming & Data Science
- Python
- Pandas
- NumPy
- Scikit-learn

### Application & Visualization
- Streamlit
- Plotly

### Model & Database
- Joblib
- SQLite

### Version Control & Deployment
- Git
- GitHub
- Streamlit Community Cloud

---

## 📸 Application Screenshots

Screenshots of the deployed application will be added here.

### 🏠 Dashboard

_Add dashboard screenshot here._

### 🤖 Churn Prediction

_Add churn prediction screenshot here._

### 🧪 Model Evaluation

_Add model evaluation screenshot here._

### 📊 Customer Analytics

_Add customer analytics screenshot here._

---

## 📁 Project Structure

```text
Customer_churn_prediction
│
├── data
│   ├── customer_churn.csv
│   ├── feature_names.pkl
│   ├── model_columns.pkl
│   └── random_forest_model.pkl
│
├── src
│   └── app.py
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 💻 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/Vishnuvardhan2231/Customer_churn_prediction.git
```

### 2. Open the project

```bash
cd Customer_churn_prediction
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the virtual environment

**Windows:**

```bash
venv\Scripts\activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the Streamlit application

```bash
streamlit run src/app.py
```

The application will open in your browser.

---

## ☁️ Deployment

The application is deployed using **Streamlit Community Cloud**.

### GitHub Repository

https://github.com/Vishnuvardhan2231/Customer_churn_prediction

### Live Application

https://customerchurnprediction-mrcximrpff4u9wy32yvufn.streamlit.app/

---

## 🎯 Project Objective

The main objective of this project is to use machine learning to identify customers who may be at risk of churn and provide an interactive dashboard for analyzing customer behavior and churn patterns.

---

## 🔮 Future Enhancements

Possible future improvements include:

- 📧 Automated customer retention notifications
- 📈 Advanced customer behavior analytics
- 🔄 Regular model retraining
- 📊 Additional machine learning models for comparison
- 🎯 Improved churn-risk segmentation
- 📱 Improved mobile responsiveness
- 🔐 More advanced user authentication and authorization

---

## 👨‍💻 Author

**Chowdam Vishnuvardhan**

Electronics & Communication Engineering

GitHub:  
https://github.com/Vishnuvardhan2231

---

⭐ If you find this project useful, consider giving the repository a star.