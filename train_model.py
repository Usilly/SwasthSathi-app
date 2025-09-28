import pandas as pd
from sklearn.model_selection import train_test_split
# --- We are now using the DecisionTreeClassifier ---
from sklearn.tree import DecisionTreeClassifier
import joblib

filename = 'symptom_data_clean.csv'
print(f"--- Starting Decision Tree Model Training using '{filename}' ---")

try:
    # Load the full dataset
    df = pd.read_csv(filename)
    print("Dataset loaded successfully. Using all {} rows.".format(len(df)))

    df.dropna(inplace=True)
    
    X = df.drop('diseases', axis=1)
    y = df['diseases']
    
    joblib.dump(X.columns, 'model_columns.pkl')
    print("Model columns saved to 'model_columns.pkl'")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print("Data split into training and testing sets.")
    
    # --- Using the DecisionTreeClassifier ---
    model = DecisionTreeClassifier(random_state=42)
    
    print("Training the Decision Tree model...")
    model.fit(X_train, y_train)
    print("Model training complete.")
    
    accuracy = model.score(X_test, y_test)
    print(f"\nModel Accuracy on Test Data: {accuracy * 100:.2f}%")
    
    joblib.dump(model, 'disease_model.pkl')
    
    print("\nSUCCESS! ✅")
    print("The Decision Tree model has been saved as 'disease_model.pkl'")

except FileNotFoundError:
    print(f"\nERROR: The file '{filename}' was not found.")
except KeyError:
    print("\nERROR: A 'diseases' column was not found in your dataset.")
except Exception as e:
    print(f"\nAn error occurred: {e}")