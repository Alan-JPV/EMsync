# train_resource_model.py (Final Version)
import pandas as pd
import xgboost as xgb
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, balanced_accuracy_score, roc_auc_score

def main():
    print("--- Training Resource Prediction Models ---")
    data = pd.read_csv('icu_interventions.csv')
    print("✅ Dataset loaded successfully.")
    
    # Correct, full list of 15 vital sign features
    vital_sign_features = [
        'mean_hr', 'min_hr', 'max_hr',
        'mean_spo2', 'min_spo2', 'max_spo2',
        'mean_temp_c', 'min_temp_c', 'max_temp_c',
        'mean_sbp', 'min_sbp', 'max_sbp',
        'mean_dbp', 'min_dbp', 'max_dbp'
    ]
    
    available_features = [f for f in vital_sign_features if f in data.columns]
    print(f"Using {len(available_features)} available vital sign features.")
    
    targets = ['ventilation_needed', 'vasopressors_needed']

    for target in targets:
        print(f"\n{'='*20} Training Model for: {target.upper()} {'='*20}")
        X = data[available_features].copy()
        y = data[target].copy()
        X = X[y.notna()]; y = y[y.notna()]
        X.fillna(X.median(), inplace=True)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum() if (y_train == 1).sum() > 0 else 1
        model = xgb.XGBClassifier(objective='binary:logistic', scale_pos_weight=scale_pos_weight, use_label_encoder=False, eval_metric='logloss', random_state=42)
        model.fit(X_train, y_train)

        preds = model.predict(X_test)
        probs = model.predict_proba(X_test)[:, 1]
        print("\n📈 Evaluation Results:")
        print(f"  - Balanced Accuracy: {balanced_accuracy_score(y_test, preds):.4f}")
        print(f"  - ROC AUC Score:     {roc_auc_score(y_test, probs):.4f}")

        # --- THIS SECTION IS NOW RESTORED ---
        model_name_prefix = target.replace('_needed', '').replace('ventilation', 'ventilator')
        
        # Feature Importance Plot
        df_imp = pd.DataFrame({'feature': available_features, 'importance': model.feature_importances_}).sort_values('importance', ascending=False)
        plt.figure(figsize=(12, 8))
        sns.barplot(x='importance', y='feature', data=df_imp.head(20), palette='viridis')
        plt.title(f'{model_name_prefix.capitalize()} Model - Feature Importance')
        plt.tight_layout()
        plot_filename = f"{model_name_prefix}_feature_importance.png"
        plt.savefig(plot_filename)
        plt.close()
        print(f"✅ Feature importance plot saved as '{plot_filename}'")
        
        # Save the model
        model_filename = f"{model_name_prefix}_model.pkl"
        joblib.dump(model, model_filename)
        print(f"✅ Model saved as '{model_filename}'")

if __name__ == "__main__":
    main()