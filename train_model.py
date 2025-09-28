import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import joblib

# The name of our dataset file
filename = 'Disease_symptom_and_patient_profile_dataset.csv'
print(f"--- Training model using '{filename}' ---")

try:
    df = pd.read_csv(filename)
    
    # Drop non-feature columns
    X = df.drop(['Disease', 'Outcome Variable'], axis=1)
    y = df['Disease']
    
    # Convert categorical text data to simple numerical data (0s and 1s)
    X = pd.get_dummies(X)
    
    # Save the exact column order and names for the app to use
    joblib.dump(X.columns, 'model_columns.pkl')
    print("Model columns saved.")

    # Initialize and train the Decision Tree model
    model = DecisionTreeClassifier(random_state=42)
    print("Training the model...")
    model.fit(X, y)
    print("Model training complete.")
    
    # Save the trained model
    joblib.dump(model, 'disease_model.pkl')
    
    print("\nSUCCESS! ✅")
    print("Lightweight model saved as 'disease_model.pkl'")

except Exception as e:
    print(f"\nAn error occurred: {e}")