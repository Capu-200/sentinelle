from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel
import uuid

from ..database import get_db
from ..models import User, Contact
from ..auth import get_current_user

router = APIRouter(
    prefix="/contacts",
    tags=["contacts"]
)

# Schemas
class ContactCreate(BaseModel):
    name: str
    email: Optional[str] = None
    iban: Optional[str] = None

class ContactResponse(BaseModel):
    contact_id: str
    name: str
    email: Optional[str] = None
    iban: Optional[str] = None
    initials: str
    is_internal: bool # True if linked to a Payon user

    class Config:
        from_attributes = True

@router.get("/", response_model=List[ContactResponse])
async def get_contacts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    stmt = select(Contact).where(Contact.user_id == current_user.user_id).order_by(Contact.name)
    contacts = db.execute(stmt).scalars().all()
    print(f"DEBUG: Fetching contacts for {current_user.email} (ID: {current_user.user_id})")
    print(f"DEBUG: Found {len(contacts)} contacts")
    
    return [
        ContactResponse(
            contact_id=c.contact_id,
            name=c.name,
            email=c.email,
            iban=c.iban,
            initials="".join([n[:1] for n in c.name.split()[:2]]).upper(),
            is_internal=c.linked_user_id is not None
        ) for c in contacts
    ]

@router.post("/", response_model=ContactResponse)
async def create_contact(
    contact_in: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Validation
    if not contact_in.email and not contact_in.iban:
        raise HTTPException(status_code=400, detail="Either Email or IBAN must be provided")

    # 2. Check duplicates
    stmt = select(Contact).where(
        Contact.user_id == current_user.user_id,
        (Contact.email == contact_in.email.lower()) if contact_in.email else (Contact.iban == contact_in.iban)
    )
    existing = db.execute(stmt).scalars().first()
    if existing:
         raise HTTPException(status_code=400, detail="Contact already exists")

    linked_user_id = None
    
    # 3. If email provided, define as P2P and try to link
    if contact_in.email:
        normalized_email = contact_in.email.lower()
        user_stmt = select(User).where(User.email == normalized_email)
        linked_user = db.execute(user_stmt).scalars().first()
        if linked_user:
            linked_user_id = linked_user.user_id

    # 4. Create
    new_contact = Contact(
        contact_id=str(uuid.uuid4()),
        user_id=current_user.user_id,
        name=contact_in.name,
        email=contact_in.email.lower() if contact_in.email else None,
        iban=contact_in.iban,
        linked_user_id=linked_user_id
    )
    
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    
    return ContactResponse(
        contact_id=new_contact.contact_id,
        name=new_contact.name,
        email=new_contact.email,
        iban=new_contact.iban,
        initials="".join([n[:1] for n in new_contact.name.split()[:2]]).upper(),
        is_internal=new_contact.linked_user_id is not None
    )

@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    print(f"DEBUG: Attempting to delete contact {contact_id} for user {current_user.user_id}")
    contact = db.get(Contact, contact_id)
    if not contact:
        print(f"DEBUG: Contact {contact_id} NOT FOUND in DB.")
    elif contact.user_id != current_user.user_id:
        print(f"DEBUG: Contact {contact_id} belongs to {contact.user_id}, not {current_user.user_id}")

    if not contact or contact.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Contact not found")
        
    db.delete(contact)
    db.commit()
    return {"status": "success"}
