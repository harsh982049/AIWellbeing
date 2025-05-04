import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

# ---------- STEP 1: Load the feature CSVs ----------
base_path = 'C:\\Users\\harsh\\OneDrive\\Desktop\\MajorProject'

keystrokes = pd.read_csv(f'{base_path}\\keystrokes_combined.csv')
mouse = pd.read_csv(f'{base_path}\\mouse_mov_speeds_combined.csv')
conditions = pd.read_csv(f'{base_path}\\usercondition_combined.csv')

# print(keystrokes_df.columns.to_list())
# print(mouse_df.columns.to_list())
# print(condition_df.columns.to_list())

# Clean column names
conditions.columns = conditions.columns.str.strip()

# Create label from Stress_Val
label_map = {"S_Stressed": 1, "V_Stressed": 1, "Neutral": 0, "F_Good": 0, "F_Great": 0}
conditions["label"] = conditions["Stress_Val"].map(label_map)

# Merge label with both datasets
keystrokes = keystrokes.merge(conditions[["SessionID", "label"]], on="SessionID", how="inner")
mouse = mouse.merge(conditions[["SessionID", "label"]], on="SessionID", how="inner")

# Group numeric features by SessionID (to get one row per session)
keystrokes_numeric = keystrokes.select_dtypes(include="number").groupby("SessionID").mean().reset_index()
mouse_numeric = mouse.select_dtypes(include="number").groupby("SessionID").mean().reset_index()
labels = conditions[["SessionID", "label"]].drop_duplicates()

# Merge all features column-wise
final_df = keystrokes_numeric.merge(mouse_numeric, on="SessionID", how="inner")
final_df = final_df.merge(labels, on="SessionID", how="inner")

# Drop missing values if any
final_df = final_df.dropna()

print(final_df.head())

# Prepare ML inputs
X = final_df.drop(columns=["SessionID", "label"])
y = final_df["label"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print("✅ Model Evaluation:")
print(classification_report(y_test, y_pred))

