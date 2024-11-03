import sqlite3
import os
def init_database():
    # 连接到 SQLite 数据库（如果数据库不存在，则会自动创建）
    conn = sqlite3.connect('models.db')

    # 创建一个游标对象
    cursor = conn.cursor()

    # 创建模型信息表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        draw_count INTEGER DEFAULT 0,
        win_count INTEGER DEFAULT 0,
        tie_count INTEGER DEFAULT 0,
        total_score REAL DEFAULT NULL
    )
    ''')

    # 获取 images 文件夹下的子文件夹名
    image_folder = 'images'
    model_names = [name for name in os.listdir(image_folder) if os.path.isdir(os.path.join(image_folder, name))]

    # 插入模型数据
    for name in model_names:
        cursor.execute('''
        SELECT COUNT(*) FROM models WHERE name = ?
        ''', (name,))
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
            INSERT INTO models (name, draw_count, win_count, tie_count, total_score)
            VALUES (?, 0, 0, 0, NULL)
            ''', (name,))

    # 提交事务
    conn.commit()

    # 关闭连接
    conn.close()
