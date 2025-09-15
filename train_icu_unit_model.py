# train_icu_unit_model.py (Corrected)
import pandas as pd
import xgboost as xgb
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder

def main():
    print("--- Training ICU Unit Prediction Model ---")
    
    # 1. Load the dataset
    try:
        data = pd.read_csv('icu_interventions_all.csv')
        print("✅ Dataset loaded successfully.")
    except FileNotFoundError:
        print("❌ ERROR: icu_interventions_all.csv not found.")
        return

    # 2. Define features and target
    # The corrected feature list including sofa_score
    vital_sign_features = [
        'mean_hr', 'min_hr', 'max_hr', 'mean_spo2', 'min_spo2', 'max_spo2',
        'mean_temp_c', 'min_temp_c', 'max_temp_c', 'mean_sbp', 'min_sbp', 'max_sbp',
        'mean_dbp', 'min_dbp', 'max_dbp', 'sofa_score'
    ]
    available_features = [f for f in vital_sign_features if f in data.columns]
    target_col = 'first_careunit'
    
    # 3. Prepare the data
    data.dropna(subset=available_features + [target_col], inplace=True)
    
    # --- THIS IS THE FIX ---
    # We will only keep ICU unit categories that have at least 100 patients
    print("Filtering out rare ICU units...")
    value_counts = data[target_col].value_counts()
    to_keep = value_counts[value_counts >= 100].index.tolist()
    data = data[data[target_col].isin(to_keep)]
    print(f"Kept {len(to_keep)} units with 100 or more patients.")
    # --- END OF FIX ---
    
    X = data[available_features]
    y_text = data[target_col]
    
    # Encode Text Labels into Numbers
    le = LabelEncoder()
    y = le.fit_transform(y_text)
    print(f"✅ Target labels ('{target_col}') encoded successfully.")
    
    # 4. Train the multi-class XGBoost model
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    model = xgb.XGBClassifier(
        objective='multi:softprob',
        num_class=len(le.classes_),
        use_label_encoder=False,
        eval_metric='mlogloss',
        random_state=42
    )
    model.fit(X_train, y_train)

    # 5. Evaluate the model
    preds = model.predict(X_test)
    print("\n📈 Model Evaluation Results:")
    print(f"  - Accuracy: {accuracy_score(y_test, preds):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, preds, target_names=le.classes_, zero_division=0))

    # 6. Save the model AND the label encoder
    joblib.dump(model, 'icu_unit_model.pkl')
    joblib.dump(le, 'icu_unit_label_encoder.pkl')
    print("\n✅ Success! Model and Label Encoder saved.")

if __name__ == "__main__":
    main()