import sqlite3

def init_master_data():
    conn = sqlite3.connect('hrm.db')
    cursor = conn.cursor()
    
    # Create languages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS languages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) UNIQUE NOT NULL,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Create technical_skills table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS technical_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) UNIQUE NOT NULL,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Insert languages
    languages = ['English', 'Spanish', 'French', 'German', 'Chinese', 'Japanese', 'Korean', 'Arabic', 'Hindi', 'Portuguese', 'Russian', 'Italian', 'Dutch', 'Swedish', 'Norwegian', 'Danish', 'Finnish', 'Polish', 'Turkish', 'Greek']
    
    for lang in languages:
        cursor.execute('INSERT OR IGNORE INTO languages (name) VALUES (?)', (lang,))
    
    # Insert technical skills
    skills = ['Adobe XD', 'Algorithms', 'Android', 'Angular', 'Ansible', 'API Design', 'Automation Testing', 'AWS', 'CSS', 'Cypress', 'Data Analysis', 'Data Visualization', 'Deep Learning', 'Django', 'Docker', 'Express.js', 'FastAPI', 'Figma', 'Flutter', 'Git', 'HTML', 'Illustrator', 'iOS', 'Java', 'JavaScript', 'Jenkins', 'Jest', 'Jupyter', 'Keras', 'Kotlin', 'Kubernetes', 'Linux', 'Machine Learning', 'Manual Testing', 'Matplotlib', 'Microservices', 'MLOps', 'Model Deployment', 'MongoDB', 'Monitoring', 'Neural Networks', 'Next.js', 'Nginx', 'NLP', 'Node.js', 'NumPy', 'OpenCV', 'Pandas', 'Performance Testing', 'Photoshop', 'Postman', 'Prototyping', 'Python', 'PyTorch', 'R', 'React', 'React Native', 'Redux', 'REST API', 'SASS', 'Scikit-learn', 'Selenium', 'Sketch', 'Spring Boot', 'SQL', 'Statistics', 'Swift', 'TensorFlow', 'Terraform', 'Test Planning', 'TestNG', 'TypeScript', 'Unit Testing', 'User Research', 'UX Design', 'Vue.js', 'Wireframing', 'Xamarin']
    
    for skill in skills:
        cursor.execute('INSERT OR IGNORE INTO technical_skills (name) VALUES (?)', (skill,))
    
    conn.commit()
    conn.close()
    print("Master data initialized successfully!")

if __name__ == "__main__":
    init_master_data()