import sys
import argparse
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    balanced_accuracy_score, f1_score
)
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

ID_COLS = {"stay_id", "stay_id_hash", "subject_id", "intime", "outtime"}
# from sklearn.model_selection import RandomizedSearchCV   #new entry
# --------------------------
# Argument parser (works in CLI + Jupyter)
# --------------------------
def parse_args():
    if any("ipykernel" in arg for arg in sys.argv):  # Running in Jupyter
        class Args:
            input = "cleaned_dataset_with_acuity.csv"
            target = "acuity"
        return Args()
    else:  # Running in terminal
        parser = argparse.ArgumentParser(description="Train ML model for ED severity prediction")
        parser.add_argument("--input", default="cleaned_dataset.csv", help="Path to dataset CSV")
        parser.add_argument("--target", default=None, help="Target column (if None, auto-detect)")
        return parser.parse_args()

# --------------------------
# Feature Engineering
# --------------------------
def add_engineered_features(df):
    df = df.copy()
    if {"heartrate", "sbp"}.issubset(df.columns):
        sbp_safe = df["sbp"].replace(0, np.nan)
        df["shock_index"] = df["heartrate"] / sbp_safe
    if {"sbp", "dbp"}.issubset(df.columns):
        df["pulse_pressure"] = df["sbp"] - df["dbp"]
    if "o2sat" in df.columns:
        df["hypoxia_flag"] = (df["o2sat"] < 90).astype(int)
    if "temperature" in df.columns:
        df["fever_flag"] = (df["temperature"] >= 38).astype(int)
    return df

def compute_sample_weights(y):
    vc = y.value_counts()
    weights = {cls: len(y) / (len(vc) * vc.loc[cls]) for cls in vc.index}
    return y.map(weights).astype(float).values

# --------------------------
# Load + prepare dataset
# --------------------------
def load_and_prepare_data(path):
    print("📊 Loading dataset...")
    df = pd.read_csv(path)
    print(f"Dataset shape: {df.shape}")
    return df

def select_features_and_target(df, target_arg):
    print("\n🎯 Preparing features and target...")
    df = add_engineered_features(df)

    target_candidates = ["esi", "ESI", "acuity", "severity", "target", "label"]
    target_column = target_arg if target_arg in df.columns else None
    if not target_column:
        target_column = next((c for c in target_candidates if c in df.columns), None)

    if target_column is None:
        print("⚠️  No target column found. Creating heuristic severity label.")
        sev = np.full(len(df), 3)
        if "heartrate" in df.columns:
            sev[df["heartrate"] >= 120] = 2
        if "o2sat" in df.columns:
            sev[df["o2sat"] <= 88] = 2
        if "temperature" in df.columns:
            sev[df["temperature"] >= 39] = 2
        if {"o2sat", "sbp"}.issubset(df.columns):
            sev[(df["o2sat"] <= 85) | (df["sbp"] <= 80)] = 1
        if "pain_median" in df.columns:
            sev[df["pain_median"] <= 2] = np.maximum(sev[df["pain_median"] <= 2], 4)
        df["severity"] = sev
        target_column = "severity"

    # Select features
    candidate_cols = []
    vital_keywords = ['hr', 'heartrate', 'heart_rate', 'temp', 'temperature',
                      'resp', 'respiratory', 'o2sat', 'oxygen', 'bp', 'systolic',
                      'diastolic', 'pain', 'shock_index', 'pulse_pressure',
                      'hypoxia_flag', 'fever_flag']
    for col in df.columns:
        low = col.lower()
        if any(k in low for k in vital_keywords):
            candidate_cols.append(col)

    for col in df.select_dtypes(include=[np.number]).columns:
        if col not in candidate_cols and col not in ID_COLS and col != target_column:
            candidate_cols.append(col)

    feature_columns = [c for c in candidate_cols if c not in ID_COLS]

    print(f"Selected features ({len(feature_columns)}): {feature_columns}")

    X = df[feature_columns].copy()
    y = df[target_column].copy()

    # --- ADD THIS BLOCK TO MAP 5 CLASSES TO 3 ---
    print("\nRemapping 5 ESI levels to 3 urgency levels...")
    # 1->0 (Critical), 2&3->1 (Moderate), 4&5->2 (Low Urgency)
    acuity_map = {1: 0, 2: 1, 3: 1, 4: 2, 5: 2}
    y = y.map(acuity_map)
    print(f"New target distribution:\n{y.value_counts().sort_index()}")
    # --- END OF BLOCK ---
    
    X = X.fillna(X.median(numeric_only=True))
    mask = ~y.isna()
    X, y = X.loc[mask], y.loc[mask]

    '''    if y.dtype.kind in "iu":
        if set(np.unique(y)).issubset({1, 2, 3, 4, 5}):
            print(f"Original target distribution:\n{y.value_counts().sort_index()}")
            y = y - 1
            print(f"Converted target distribution:\n{y.value_counts().sort_index()}")
    else:
        y = y.astype("category").cat.codes'''

    print(f"Final dataset shape: X={X.shape}, y={y.shape}")
    return X, y, feature_columns

# --------------------------
# Train models
# --------------------------
def train_models(X, y):
    print("\n🤖 Training ML models...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Train: {X_train.shape}, Test: {X_test.shape}")

    sample_weights_train = compute_sample_weights(y_train)
    models, results = {}, {}

    print("\n🔹 Training Random Forest...")
    rf_model = RandomForestClassifier(
        n_estimators=300, random_state=42, n_jobs=-1, class_weight="balanced"
    )
    rf_model.fit(X_train, y_train)
    rf_pred = rf_model.predict(X_test)

    results['Random Forest'] = {
        'accuracy': accuracy_score(y_test, rf_pred),
        'balanced_accuracy': balanced_accuracy_score(y_test, rf_pred),
        'macro_f1': f1_score(y_test, rf_pred, average="macro"),
        'predictions': rf_pred,
        'feature_importance': rf_model.feature_importances_
    }
    models['Random Forest'] = rf_model

    print("🔹 Training XGBoost...")
    xgb_model = xgb.XGBClassifier(
        objective="multi:softprob",
        num_class=len(np.unique(y)),
        n_estimators=500,
        max_depth=6,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        tree_method="hist",
        random_state=42,
        n_jobs=-1,
        eval_metric="mlogloss"
    )
    xgb_model.fit(X_train, y_train, sample_weight=sample_weights_train)
    xgb_pred = xgb_model.predict(X_test)

    cv_scores = cross_val_score(
        xgb_model, X, y, cv=5, scoring="f1_macro", n_jobs=-1
    )
    print(f"XGBoost CV Macro-F1: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    results['XGBoost'] = {
        'accuracy': accuracy_score(y_test, xgb_pred),
        'balanced_accuracy': balanced_accuracy_score(y_test, xgb_pred),
        'macro_f1': f1_score(y_test, xgb_pred, average="macro"),
        'predictions': xgb_pred,
        'feature_importance': xgb_model.feature_importances_
    }
    models['XGBoost'] = xgb_model

    return models, results, X_test, y_test, X_train.columns

# --------------------------
# Evaluate models
# --------------------------
'''def evaluate_models(models, results, X_test, y_test, feature_names):
    print("\n📈 Model Evaluation Results:")
    best_model_name, best_score = None, -1.0

    for name, res in results.items():
        acc, bal, f1m = res['accuracy'], res['balanced_accuracy'], res['macro_f1']
        print(f"\n🔸 {name}: Acc={acc:.4f}, BalAcc={bal:.4f}, Macro-F1={f1m:.4f}")

        preds_os = res['predictions'] + 1
        ytest_os = y_test + 1
        print(classification_report(
            ytest_os, preds_os, zero_division=0,
            target_names=['ESI-1','ESI-2','ESI-3','ESI-4','ESI-5']
        ))

        cm = confusion_matrix(ytest_os, preds_os)
        plt.figure(figsize=(6,5))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                    xticklabels=['ESI-1','ESI-2','ESI-3','ESI-4','ESI-5'],
                    yticklabels=['ESI-1','ESI-2','ESI-3','ESI-4','ESI-5'])
        plt.title(f"Confusion Matrix - {name}")
        plt.savefig(f"confusion_matrix_{name}.png", dpi=150)
        plt.close()

        if f1m > best_score:
            best_score = f1m
            best_model_name = name

    print(f"\n🏆 Best Model: {best_model_name} (Macro-F1={best_score:.4f})")
    return best_model_name, models[best_model_name]
'''
# --------------------------
def evaluate_models(models, results, X_test, y_test, feature_names):
    print("\n📈 Model Evaluation Results:")
    best_model_name, best_score = None, -1.0

    # Define the names for our new 3 classes
    new_target_names = ['Critical (0)', 'Moderate (1)', 'Low Urgency (2)']

    for name, res in results.items():
        acc, bal, f1m = res['accuracy'], res['balanced_accuracy'], res['macro_f1']
        print(f"\n🔸 {name}: Acc={acc:.4f}, BalAcc={bal:.4f}, Macro-F1={f1m:.4f}")

        # Use the new target names and the direct model predictions (no more +1 offset)
        print(classification_report(
            y_test, res['predictions'], zero_division=0,
            target_names=new_target_names
        ))

        cm = confusion_matrix(y_test, res['predictions'])
        plt.figure(figsize=(6,5))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                    xticklabels=new_target_names,
                    yticklabels=new_target_names)
        plt.title(f"Confusion Matrix - {name}")
        plt.savefig(f"confusion_matrix_{name}.png", dpi=150)
        plt.close()

        if f1m > best_score:
            best_score = f1m
            best_model_name = name

    print(f"\n🏆 Best Model: {best_model_name} (Macro-F1={best_score:.4f})")
    return best_model_name, models[best_model_name]

# --------------------------
# Save model + report
# --------------------------
'''class ESIPredictionWrapper:
    def __init__(self, model):
        self.model = model
    def predict(self, X):
        return self.model.predict(X) + 1
    def predict_proba(self, X):
        return self.model.predict_proba(X)'''

def save_model_and_report(best_model_name, best_model, results, feature_names, y):
    print(f"\n💾 Saving best model: {best_model_name}")
    '''wrapped = ESIPredictionWrapper(best_model)'''
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_file = f"best_model_{timestamp}.pkl"
    '''joblib.dump(wrapped, model_file)'''
    joblib.dump(best_model, model_file)

    label_map = {i: i+1 for i in range(len(np.unique(y)))}
    joblib.dump(label_map, "label_map.pkl")

    print(f"✅ Model saved as {model_file}")

    with open('training_report.txt', 'w', encoding='utf-8') as f:
        f.write("MEDICAL ML MODEL TRAINING REPORT\n")
        f.write("="*50 + "\n\n")
        f.write(f"Best Model: {best_model_name}\n\n")
        for name, res in results.items():
            f.write(f"{name}:\n")
            f.write(f"  Accuracy: {res['accuracy']:.4f}\n")
            f.write(f"  Balanced Accuracy: {res['balanced_accuracy']:.4f}\n")
            f.write(f"  Macro-F1: {res['macro_f1']:.4f}\n\n")
        f.write("Artifacts:\n")
        f.write(f" - {model_file}\n - label_map.pkl\n")
        f.write(" - confusion_matrix_[model].png\n")

# --------------------------
# Plot Feature Importance
# --------------------------
def plot_feature_importance(results, feature_names):
    print("\n📊 Plotting feature importance...")

    # Find the XGBoost results key
    xgb_key = next((k for k in results if 'XGBoost' in k), None)
    if not xgb_key:
        print("Could not find XGBoost results to plot importance.")
        return

    importances = results[xgb_key]['feature_importance']

    # Create a DataFrame for easy sorting and plotting
    feature_importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importances
    }).sort_values(by='importance', ascending=False)

    # Create the bar plot
    plt.figure(figsize=(12, 8))
    sns.barplot(x='importance', y='feature', data=feature_importance_df, palette='viridis')
    plt.title('XGBoost Feature Importance', fontsize=16)
    plt.xlabel('Importance Score', fontsize=12)
    plt.ylabel('Feature', fontsize=12)
    plt.tight_layout()

    # Save the plot to a file
    plt.savefig('feature_importance.png', dpi=150)
    plt.close()
    print("✅ Feature importance plot saved as 'feature_importance.png'")

# --------------------------
# Main
# --------------------------
def main():
    print("🚀 MEDICAL ML MODEL TRAINING PIPELINE")
    print("="*50)

    args = parse_args()
    try:
        df = load_and_prepare_data(args.input)
        X, y, feature_names = select_features_and_target(df, args.target)
        models, results, X_test, y_test, feature_names = train_models(X, y)
        best_model_name, best_model = evaluate_models(models, results, X_test, y_test, feature_names)
        plot_feature_importance(results, feature_names) #newline
        save_model_and_report(best_model_name, best_model, results, feature_names, y)

        print("\n✅ Pipeline finished. Artifacts created.")

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    main()
