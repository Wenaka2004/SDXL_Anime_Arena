import pandas as pd
import json

def extract_characters(input_file, output_file):
    # 读取 Excel 文件
    df = pd.read_excel(input_file)
    
    # 提取需要的列并转换为字典列表
    extracted = []
    for _, row in df.iterrows():
        character_tag = row.get('character_tag')
        character_str_tag = row.get('character_str_tag')
        if pd.notna(character_tag) and pd.notna(character_str_tag):
            extracted.append({
                'character_tag': character_tag,
                'character_str_tag': character_str_tag
            })
    
    # 保存为 JSON 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(extracted, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    extract_characters('character_sanaeXL_v1_character_ccip0.8.xlsx', 'extracted_characters.json')