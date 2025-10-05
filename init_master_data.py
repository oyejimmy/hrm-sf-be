from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Language, TechnicalSkill
from app.database import Base

# Create tables
Base.metadata.create_all(bind=engine)

def init_languages():
    db = SessionLocal()
    try:
        languages = ['English', 'Spanish', 'French', 'German', 'Chinese', 'Japanese', 'Korean', 'Arabic', 'Hindi', 'Portuguese', 'Russian', 'Italian', 'Dutch', 'Swedish', 'Norwegian', 'Danish', 'Finnish', 'Polish', 'Turkish', 'Greek']
        
        for lang_name in languages:
            existing = db.query(Language).filter(Language.name == lang_name).first()
            if not existing:
                language = Language(name=lang_name)
                db.add(language)
        
        db.commit()
        print("Languages initialized successfully!")
    except Exception as e:
        print(f"Error initializing languages: {e}")
        db.rollback()
    finally:
        db.close()

def init_technical_skills():
    db = SessionLocal()
    try:
        skills = ['Adobe XD', 'Algorithms', 'Android', 'Angular', 'Ansible', 'API Design', 'Automation Testing', 'AWS', 'CSS', 'Cypress', 'Data Analysis', 'Data Visualization', 'Deep Learning', 'Django', 'Docker', 'Express.js', 'FastAPI', 'Figma', 'Flutter', 'Git', 'HTML', 'Illustrator', 'iOS', 'Java', 'JavaScript', 'Jenkins', 'Jest', 'Jupyter', 'Keras', 'Kotlin', 'Kubernetes', 'Linux', 'Machine Learning', 'Manual Testing', 'Matplotlib', 'Microservices', 'MLOps', 'Model Deployment', 'MongoDB', 'Monitoring', 'Neural Networks', 'Next.js', 'Nginx', 'NLP', 'Node.js', 'NumPy', 'OpenCV', 'Pandas', 'Performance Testing', 'Photoshop', 'Postman', 'Prototyping', 'Python', 'PyTorch', 'R', 'React', 'React Native', 'Redux', 'REST API', 'SASS', 'Scikit-learn', 'Selenium', 'Sketch', 'Spring Boot', 'SQL', 'Statistics', 'Swift', 'TensorFlow', 'Terraform', 'Test Planning', 'TestNG', 'TypeScript', 'Unit Testing', 'User Research', 'UX Design', 'Vue.js', 'Wireframing', 'Xamarin']
        
        for skill_name in skills:
            existing = db.query(TechnicalSkill).filter(TechnicalSkill.name == skill_name).first()
            if not existing:
                skill = TechnicalSkill(name=skill_name)
                db.add(skill)
        
        db.commit()
        print("Technical skills initialized successfully!")
    except Exception as e:
        print(f"Error initializing technical skills: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_languages()
    init_technical_skills()
    print("Master data initialization completed!")