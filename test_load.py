import pandas as pd
import os

csv_filename = "dados_filtrados_completos.xlsx - Sheet1.csv"
print("File exists:", os.path.exists(csv_filename))

try:
    df = pd.read_csv(csv_filename, encoding='utf-8')
    print("Shape after read_csv:", df.shape)
    
    # Coordinates cleaning
    df['Latitude'] = df['Latitude'].astype(str).str.replace(',', '.').astype(float)
    df['Longitude'] = df['Longitude'].astype(str).str.replace(',', '.').astype(float)
    
    # Remove NaN coords
    df = df.dropna(subset=['Latitude', 'Longitude'])
    print("Shape after cleaning coords:", df.shape)
    
    # Convert types
    for col in ['A', 'B', 'C', 'D', 'E', 'F', 'total_exames', 'total_alunos', 'ANO']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    print("Successfully loaded real data! No errors.")
except Exception as e:
    print("Error encountered:", e)
