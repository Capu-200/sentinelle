from dotenv import load_dotenv
load_dotenv()

from sqlmodel import Session, select

from app.database import engine
from app.models import User, Wallet, Transaction

with Session(engine) as session:
    print("\n--- ANALYSE UTILISATEURS ---")
    users = session.exec(select(User)).all()
    for u in users:
        print(f"User: {u.email} | Country Home: '{u.country_home}'")
        
    print("\n--- ANALYSE TRANSACTIONS ---")
    txs = session.exec(select(Transaction).limit(5)).all()
    for t in txs:
        # Check logic as per get_transactions
        src_country = "N/A"
        dst_country = "N/A"
        
        if t.initiator_user_id:
            init = session.get(User, t.initiator_user_id)
            if init: src_country = init.country_home
            
        if t.destination_wallet_id:
            w = session.get(Wallet, t.destination_wallet_id)
            if w and w.user_id:
                u = session.get(User, w.user_id)
                if u: dst_country = u.country_home
                
        print(f"TX {t.transaction_id[:8]}... | Source: {src_country} | Dest: {dst_country}")
