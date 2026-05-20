from app import app, db, Product
import traceback

print(f"URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

with app.app_context():
    try:
        count = Product.query.count()
        print(f"Initial count: {count}")
        
        test_product = Product(name='TempTestProduct')
        # Buscando campos mínimos mirando la salida anterior. Solo vi name.
        # Asumiremos que name es lo mínimo viendo la definición anterior.
        db.session.add(test_product)
        db.session.commit()
        print("Commit successful")
        
        p = Product.query.filter_by(name='TempTestProduct').first()
        if p:
            print(f"Found product: {p.name}")
            db.session.delete(p)
            db.session.commit()
            print("Cleaned up")
        else:
            print("Product not found after commit")
            
    except Exception:
        print("Error during DB operations:")
        traceback.print_exc()
