import os
from fastapi import FastAPI, Depends, HTTPException,Form, Query
from sqlalchemy.orm import Session,joinedload
import redis
import json
from database import engine, Base, SessionLocal
from models import User, Product, Category, Order, OrderItem,ItemOrder,CreateOrderRequest
from passlib.context import CryptContext
from typing import Optional,List

# Kreiranje baze podataka (ako već ne postoji)
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Postavljanje postavki za spajanje na bazu podataka i Redis
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)

# Provjera povezanosti s Redisom
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    redis_client.ping()
except redis.ConnectionError:
    raise HTTPException(status_code=500, detail="Nije moguće povezati se s Redis poslužiteljem")

# Funkcija za dobivanje sesije baze podataka
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Inicijalizacija za hashiranje lozinki
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Funkcija za hashiranje lozinke."""
    return pwd_context.hash(password)

# Pomoćna funkcija za pretvaranje objekta u rječnik (bez metapodataka SQLAlchemy-a)
def item_to_dict(item):
    item_dict = item.__dict__
    if '_sa_instance_state' in item_dict:
        del item_dict['_sa_instance_state']
    return item_dict

# User Routes
@app.get("/users/")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    if not users:
        return {"message": "No users found"}
    return {"users": [item_to_dict(user) for user in users]}

@app.post("/users/")
def create_user(username: str, email: str, password: str, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = hash_password(password)
    user = User(username=username, email=email, password_hash=hashed_password)
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    redis_client.delete(f"user_{user.id}")  
    return {"user": item_to_dict(user)}

@app.get("/users/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
  
    cached_user = redis_client.get(f"user_{user_id}")
    if cached_user:
        return {"user": json.loads(cached_user), "redis_debug": "Keširanje uspješno!"}

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    redis_client.set(f"user_{user_id}", json.dumps(item_to_dict(user)))
    return {"user": item_to_dict(user)}

@app.put("/users/{user_id}")
def update_user(user_id: int, username: str = None, email: str = None, password: str = None, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.username = username if username is not None else user.username
    user.email = email if email is not None else user.email

    if password:
        user.password_hash = hash_password(password)

    db.commit()
    db.refresh(user)

    redis_client.delete(f"user_{user_id}")
    redis_client.set(f"user_{user_id}", json.dumps(item_to_dict(user)))
    return {"user": item_to_dict(user)}

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    redis_client.delete(f"user_{user_id}") 
    return {"message": "User deleted"}

# Product Routes
@app.get("/products/")
def get_all_products(db: Session = Depends(get_db)):
  
    products = db.query(Product).all()
    product_list = [item_to_dict(product) for product in products]

    return {"products": product_list}

@app.post("/products/")
def create_product(name: str, description: str, price: int, category_id: int, db: Session = Depends(get_db)):
    product = Product(name=name, description=description, price=price, category_id=category_id)

    db.add(product)
    db.commit()
    db.refresh(product)

    redis_client.delete(f"product_{product.id}")
    return {"product": item_to_dict(product)}

@app.get("/products/{product_id}")
def read_product(product_id: int, db: Session = Depends(get_db)):
  
    cached_product = redis_client.get(f"product_{product_id}")
    if cached_product:
        return {"product": json.loads(cached_product), "redis_debug": "Keširanje uspješno!"}

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    redis_client.set(f"product_{product_id}", json.dumps(item_to_dict(product)))
    return {"product": item_to_dict(product)}

@app.put("/products/{product_id}")
def update_product(product_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    price: Optional[float] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.name = name if name is not None else product.name
    product.description = description if description is not None else product.description
    product.price = price if price is not None else product.price
    product.category_id = category_id if category_id is not None else product.category_id

    db.commit()
    db.refresh(product)

    redis_client.delete(f"product_{product_id}")
    redis_client.set(f"product_{product_id}", json.dumps(item_to_dict(product)))
    return {"product": item_to_dict(product)}

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()

    redis_client.delete(f"product_{product_id}")
    return {"message": "Product deleted"}

# Rute za Kategorije
@app.get("/categories/")
def get_all_categories(db: Session = Depends(get_db)):
    
    categories = db.query(Category).all()
    category_list = [item_to_dict(category) for category in categories]
    return {"categories": category_list}

@app.post("/categories/")
def create_category(name: str, db: Session = Depends(get_db)):
    category = Category(name=name)
    
    db.add(category)
    db.commit()
    db.refresh(category)

    redis_client.set(f"category:{category.id}", json.dumps(item_to_dict(category)))
    return {"category": item_to_dict(category)}

@app.get("/categories/{category_id}")
def read_category(category_id: int, db: Session = Depends(get_db)):
  
    cached_category = redis_client.get(f"category:{category_id}")
    if cached_category:
        return {"category": json.loads(cached_category), "redis_debug": "Keširanje uspješno!"}

    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    redis_client.set(f"category:{category.id}", json.dumps(item_to_dict(category)))
    return {"category": item_to_dict(category)}

@app.put("/categories/{category_id}")
def update_category(category_id: int, name: str, db: Session = Depends(get_db)):
   
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    category.name = name
    db.commit()
    db.refresh(category)

    redis_client.delete(f"category:{category_id}")
    redis_client.set(f"category:{category.id}", json.dumps(item_to_dict(category)))

    return {"category": item_to_dict(category)}

@app.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
  
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category)
    db.commit()

    redis_client.delete(f"category:{category_id}")
    return {"message": "Category deleted"}

# Rute za narudžbe

@app.get("/orders_with_items/")
def get_all_orders_with_items(db: Session = Depends(get_db)):
    # Fetch all orders with their items
    orders = db.query(Order).options(joinedload(Order.order_items)).all()

    result = [
        {
            "order_id": order.id,
            "user_id": order.user_id,
            "total_price": order.total_price,
            "order_items": [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "price": item.price  # Total price for this item
                }
                for item in order.order_items
            ]
        }
        for order in orders
    ]

    return {"orders": result}


@app.post("/orders_with_items/")
def create_order_with_items(order_request: CreateOrderRequest, db: Session = Depends(get_db)):
    if not order_request.items:
        raise HTTPException(status_code=400, detail="Order must have at least one item")

    total_price = 0

    new_order = Order(user_id=order_request.user_id, total_price=0)
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    for item in order_request.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with ID {item.product_id} not found")

        item_price = product.price * item.quantity
        total_price += item_price

        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item_price
        )
        db.add(order_item)

    new_order.total_price = total_price
    db.commit()

    return {
        "order": {
            "order_id": new_order.id,
            "user_id": new_order.user_id,
            "total_price": new_order.total_price
        }
    }

@app.put("/orders_with_items/{order_id}")
def update_order_with_items(order_id: int, items: List[ItemOrder], db: Session = Depends(get_db)):
    # Dohvati narudžbu prema order_id
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Dohvati sve postojeće stavke narudžbe
    existing_order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()

    total_price = 0
    order_items = []

    for item in items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with ID {item.product_id} not found")

        price = product.price  # Jedinična cijena proizvoda, uvijek definirana na početku petlje

        # Provjeri postoji li već stavka za taj proizvod
        existing_item = next((oi for oi in existing_order_items if oi.product_id == item.product_id), None)

        if existing_item:
            # Ako stavka već postoji, ažuriraj ju
            existing_item.quantity = item.quantity
            existing_item.price = price  # Postavi cijenu na cijenu jednog proizvoda
            db.add(existing_item)  # Dodaj izmijenjenu stavku
            db.commit()  # Potvrdi promjene u bazi
            db.refresh(existing_item)  # Osvježi promijenjenu stavku kako bi dobio nove podatke
            order_items.append(existing_item)  # Dodaj ažuriranu stavku u odgovor
        else:
            # Ako stavka ne postoji, kreiraj novu
            order_item = OrderItem(
                order_id=order.id,  # Poveži stavku s narudžbom
                product_id=item.product_id,
                quantity=item.quantity,
                price=price
            )
            db.add(order_item)
            db.commit()  # Spremi novu stavku
            db.refresh(order_item)  # Osvježi novu stavku kako bi dobio novi ID
            order_items.append(order_item)  # Dodaj novu stavku u odgovor

        # Izračunavanje ukupne cijene narudžbe
        total_price += price * item.quantity

    # Ažuriraj ukupnu cijenu narudžbe
    order.total_price = total_price
    db.commit()  # Spremi promjenu ukupne cijene narudžbe

    # Priprema odgovora s detaljima narudžbe i stavki
    order_items_response = [
        {
            "product_id": item.product_id,
            "quantity": item.quantity,
            "price": item.price
        }
        for item in order_items
    ]

    return {
        "order": {
            "order_id": order.id,  
            "user_id": order.user_id,
            "total_price": order.total_price
        },
        "order_items": order_items_response
    }


@app.get("/orders_with_items/{order_id}")
def read_order_with_items(order_id: int, db: Session = Depends(get_db)):
    # Fetch the order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()

    order_items_response = [
        {
            "product_id": item.product_id,
            "quantity": item.quantity,
            "price": item.price  # Total price for this item
        }
        for item in order_items
    ]

    return {
        "order": {
            "order_id": order.id,
            "user_id": order.user_id,
            "total_price": order.total_price
        },
        "order_items": order_items_response
    }

@app.delete("/orders_with_items/{order_id}")
def delete_order_with_items(order_id: int, db: Session = Depends(get_db)):
    # Fetch the order by ID
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    db.query(OrderItem).filter(OrderItem.order_id == order_id).delete()
    db.delete(order)
    db.commit()

    return {"message": "Order and associated order items deleted"}