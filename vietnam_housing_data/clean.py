import numpy as np
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_csv('housing_clean.csv')
print("số dòng ban đầu:", len(df))

text_columns = ['Province', 'District', 'Ward', 'Street', 'Project', 'House_Direction', 'Balcony_Direction', 'Legal_Status', 'Furniture_State']

for col in text_columns:
    if col in df.columns:
        df[col] = df[col].fillna('Unknown').astype(str).str.strip()
        
dieu_kien_loi_mat_tien = (df['Frontage'] > 15) & (df['Frontage'] > df['Area'] * 0.4)

df.loc[dieu_kien_loi_mat_tien, 'Frontage'] = df.loc[dieu_kien_loi_mat_tien, 'Frontage'] / 10

dieu_kien_loi_dien_tich = (df['Access_Road'] > 25) & (df['Area'] < 100)
df.loc[dieu_kien_loi_dien_tich, 'Access_Road'] = df.loc[dieu_kien_loi_dien_tich, 'Access_Road'] / 10

df['Frontage'] = df['Frontage'].fillna(0)

df['Floors'] = df['Floors'].fillna(df['Floors'].median())
df['Bedrooms'] = df['Bedrooms'].fillna(df['Bedrooms'].median())
df['Bathrooms'] = df['Bathrooms'].fillna(df['Bathrooms'].median())

df['Access_Road'] = df['Access_Road'].fillna(df.groupby('District')['Access_Road'].transform('median'))
df['Access_Road'] = df['Access_Road'].fillna(df['Access_Road'].median())

dong_phi_ly_1 = (df['Floors'] == 1) & (df['Bedrooms'] > 5)
dong_phi_ly_2 = (df['Area'] < 20) & (df['Bedrooms'] > 4)

df = df[~(dong_phi_ly_1 | dong_phi_ly_2)].copy()
print("số dòng sau khi loại bỏ:", len(df))

df['Total_Floors_Area_m2'] = df['Area'] * df['Floors']
df['Price_per_m2_Million'] = (df['Price'] * 1000 /  df['Area']).round(2)

ten_cot_moi = {
    'Address': 'Full_Address',
    'Area': 'Land_Area_m2',
    'Frontage': 'Frontage_m',
    'Access_Road': 'Access_Road_m',
    'Floors': 'Floors_Count',
    'Bedrooms': 'Bedrooms_Count',
    'Bathrooms': 'Bathrooms_Count',
    'Price': 'Price_Billion_VND'
}
df = df.rename(columns=ten_cot_moi)

df = df.reset_index(drop=True)
df['Property_ID'] = [f"VN_HOUSE_{i+1:05d}" for i in range(len(df))]

so_o_trong = df.isnull().sum().sum()
if so_o_trong > 0:
    print(f"cảnh báo: còn {so_o_trong} ô trống")
else:
    print("không còn ô trống")
    
ten_file_moi = "house_cleaned.csv"
df.to_csv(ten_file_moi, index=False, encoding='utf-8-sig')
print(f"Dữ liệu đã được làm sạch và lưu vào file: {ten_file_moi}")