Customer Churn Prediction - Deployment Package

Included:
- src/app.py
- requirements.txt

Before running, place these required application data/model files in data/:
- customer_churn.csv
- random_forest_model.pkl
- model_columns.pkl
- feature_names.pkl

Keep these private/local unless you have a secure deployment plan:
- users.db
- customer_churn_history.db

Run:
  pip install -r requirements.txt
  streamlit run src/app.py
