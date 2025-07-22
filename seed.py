# seed.py
from app import app, db
from models import User, Customer, ServicePlan, Subscription, NetworkNode
from datetime import datetime, timedelta

def seed():
    with app.app_context():
        db.create_all()
        
        # Create users if they don't exist
        if not User.query.first():
            # Admin user
            admin = User(username='admin', email='admin@example.com', role='admin')
            admin.set_password('admin123')
            
            # Sales user
            sales = User(username='sales', email='sales@example.com', role='sales')
            sales.set_password('sales123')
            
            # Tech support user
            tech = User(username='tech', email='tech@example.com', role='tech')
            tech.set_password('tech123')
            
            # Customer users
            customer1 = User(username='customer1', email='customer1@example.com', role='customer')
            customer1.set_password('customer123')
            
            customer2 = User(username='customer2', email='customer2@example.com', role='customer')
            customer2.set_password('customer123')

            db.session.add_all([admin, sales, tech, customer1, customer2])
            db.session.commit()
            
            # Create customer profiles
            cust1 = Customer(
                user_id=customer1.id,
                name='John Doe',
                email='customer1@example.com',
                phone='+1234567890',
                billing_address={'street': '123 Main St', 'city': 'Anytown', 'zip': '12345'},
                service_address={'street': '123 Main St', 'city': 'Anytown', 'zip': '12345'}
            )
            
            cust2 = Customer(
                user_id=customer2.id,
                name='Jane Smith',
                email='customer2@example.com',
                phone='+1234567891',
                billing_address={'street': '456 Oak Ave', 'city': 'Somewhere', 'zip': '67890'},
                service_address={'street': '456 Oak Ave', 'city': 'Somewhere', 'zip': '67890'}
            )
            
            db.session.add_all([cust1, cust2])
            db.session.commit()
            
            # Create service plans
            plans = [
                ServicePlan(
                    name='Basic Internet',
                    description='Perfect for light browsing and email',
                    speed='25 Mbps',
                    data_cap='500 GB',
                    price=29.99,
                    is_active=True
                ),
                ServicePlan(
                    name='Standard Internet',
                    description='Great for streaming and gaming',
                    speed='100 Mbps',
                    data_cap='Unlimited',
                    price=49.99,
                    is_active=True
                ),
                ServicePlan(
                    name='Premium Internet',
                    description='Ultra-fast for heavy users',
                    speed='1 Gbps',
                    data_cap='Unlimited',
                    price=99.99,
                    is_active=True
                )
            ]
            
            db.session.add_all(plans)
            db.session.commit()
            
            # Create sample subscriptions
            sub1 = Subscription(
                customer_id=cust1.id,
                plan_id=plans[1].id,  # Standard plan
                start_date=datetime.utcnow() - timedelta(days=30),
                end_date=datetime.utcnow() + timedelta(days=30),
                status='active',
                payment_method='credit_card'
            )
            
            sub2 = Subscription(
                customer_id=cust2.id,
                plan_id=plans[0].id,  # Basic plan
                start_date=datetime.utcnow() - timedelta(days=15),
                end_date=datetime.utcnow() + timedelta(days=45),
                status='active',
                payment_method='bank_transfer'
            )
            
            db.session.add_all([sub1, sub2])
            db.session.commit()
            
            # Create network nodes
            nodes = [
                NetworkNode(
                    name='Central Hub',
                    location={'address': 'Downtown Data Center', 'lat': 40.7128, 'lng': -74.0060},
                    status='active',
                    capacity=1000,
                    current_load=750
                ),
                NetworkNode(
                    name='North Tower',
                    location={'address': 'North Side Tower', 'lat': 40.7589, 'lng': -73.9851},
                    status='active',
                    capacity=500,
                    current_load=300
                ),
                NetworkNode(
                    name='South Station',
                    location={'address': 'South Distribution Point', 'lat': 40.6892, 'lng': -74.0445},
                    status='maintenance',
                    capacity=750,
                    current_load=0
                )
            ]
            
            db.session.add_all(nodes)
            db.session.commit()

            print("Database seeded successfully!")
            print("Users created:")
            print("- admin/admin123 (Admin)")
            print("- sales/sales123 (Sales)")
            print("- tech/tech123 (Tech Support)")
            print("- customer1/customer123 (Customer)")
            print("- customer2/customer123 (Customer)")

if __name__ == '__main__':
    seed()