import sys
from sqlmodel import Session, select, create_engine
from app.models import User
from app.auth import get_password_hash

DATABASE_URL = "postgresql+psycopg2://fraud_user:MaSuperBase2024!Secure@127.0.0.1:5433/fraud_db"

def reset_password(email="jacques@payon.app", new_password="password123"):
    engine = create_engine(DATABASE_URL)
    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        user = session.execute(statement).scalars().first()
        
        if not user:
            print(f"ERROR: User {email} not found.")
            return
            
        user.hashed_password = get_password_hash(new_password)
        session.add(user)
        session.commit()
        print(f"SUCCESS: Password for {email} has been reset to: {new_password}")

if __name__ == "__main__":
    email_to_reset = sys.argv[1] if len(sys.argv) > 1 else "jacques@payon.app"
    pwd_to_set = sys.argv[2] if len(sys.argv) > 2 else "password123"
    reset_password(email_to_reset, pwd_to_set)
