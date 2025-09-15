# train_all_models.py (with SMOTE)
import pandas as pd
import xgboost as xgb
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, balanced_accuracy_score, roc_auc_score
from imblearn.over_sampling import SMOTE # Import the new library

def main():
    print("--- Training Resource Prediction Models with SMOTE ---")
    data = pd.read_csv('icu_interventions_all.csv')
    
    vital_sign_features = [
        'mean_hr', 'min_hr', 'max_hr', 'mean_spo2', 'min_spo2', 'max_spo2',
        'mean_temp_c', 'min_temp_c', 'max_temp_c', 'mean_sbp', 'min_sbp', 'max_sbp',
        'mean_dbp', 'min_dbp', 'max_dbp'
    ]
    available_features = [f for f in vital_sign_features if f in data.columns]
    
    # Let's train the 3 models we need to fix
    targets = ['dialysis_needed', 'sedatives_needed', 'opioids_needed']

    for target in targets:
        print(f"\n{'='*20} Training Model for: {target.upper()} {'='*20}")
        
        X = data[available_features].copy()
        y = data[target].copy()
        
        X = X[y.notna()]; y = y[y.notna()]
        X.fillna(X.median(), inplace=True)

        if len(y.unique()) < 2:
            print(f"Target '{target}' has only one class. Skipping.")
            continue

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        # --- THIS IS THE NEW SMOTE STEP ---
        print(f"Original training distribution:\n{y_train.value_counts()}")
        smote = SMOTE(random_state=42)
        X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
        print(f"Resampled training distribution:\n{y_train_resampled.value_counts()}")
        # --- END OF NEW STEP ---

        # We remove scale_pos_weight because SMOTE is handling the balancing
        model = xgb.XGBClassifier(
            objective='binary:logistic',
            use_label_encoder=False,
            eval_metric='logloss',
            random_state=42
        )
        # Train on the NEW, resampled data
        model.fit(X_train_resampled, y_train_resampled)

        preds = model.predict(X_test)
        probs = model.predict_proba(X_test)[:, 1]
        print("\n📈 Evaluation Results:")
        print(f"  - Balanced Accuracy: {balanced_accuracy_score(y_test, preds):.4f}")
        print(f"  - ROC AUC Score:     {roc_auc_score(y_test, probs):.4f}")

        model_filename = f"{target.replace('_needed', '')}_model.pkl"
        joblib.dump(model, model_filename)
        print(f"\n✅ Success! Model saved as '{model_filename}'")

if __name__ == "__main__":
    main()