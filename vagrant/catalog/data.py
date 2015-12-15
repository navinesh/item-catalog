# Create dummy data
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Base, Item, User

engine = create_engine('postgresql:///itemcatalog')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create user
User1 = User(name="Navinesh Chand", email="navinesh@example.com",
             picture='https://lh6.googleusercontent.com/-2fEcJXq3h2w/AAAAAAAAAAI/AAAAAAAAAZQ/wGnV_4kWiOg/photo.jpg')
session.add(User1)
session.commit()

# Create category
category1 = Category(user_id=1, name="Soccer")

session.add(category1)
session.commit()

# Create items
Item3 = Item(user_id=1, name="Soccer shin pad", description="A shin guard or shin pad is a piece of equipment worn on the front of a player\'s shin to protect them from injury.",
             url="soccer_shin_pad.jpg", category=category1)

session.add(Item3)
session.commit()

Item2 = Item(user_id=1, name="Soccer ball", description="A football, soccer ball, or association football ball is the ball used in the sport of association football. The name of the ball varies according to whether the sport is called \"football\", \"soccer\", or \"association football\".",
             url="soccer_ball.jpg", category=category1)

session.add(Item2)
session.commit()

Item1 = Item(user_id=1, name="Soccer boot", description="Football boots, called cleats or soccer shoes in North America, are an item of footwear worn when playing football. Those designed for grass pitches have studs on the outsole to aid grip.",
             url="soccer_boot.png", category=category1)

session.add(Item1)
session.commit()

# Create category
category2 = Category(user_id=1, name="Rugby")

session.add(category2)
session.commit()

# Create items
Item2 = Item(user_id=1, name="Rugby jersey", description="A rugby shirt is a shirt worn by players of rugby union or rugby league. It usually has short sleeves, though long sleeves are common as well.",
             url="rugby_jersey.jpg", category=category2)

session.add(Item2)
session.commit()

Item1 = Item(user_id=1, name="Rugby ball", description="A rugby ball, originally called a quanco, is a diamond shape ball used for easier passing.",
             url="Rugby_ball.jpg", category=category2)

session.add(Item1)
session.commit()

# Create category
category3 = Category(user_id=1, name="Basket ball")

session.add(category3)
session.commit()

# Create items
Item1 = Item(user_id=1, name="Basketball", description="A basketball is a spherical inflated ball used in a game of basketball.",
             url="basketball.png", category=category3)

session.add(Item1)
session.commit()

# Create category
category4 = Category(user_id=1, name="Tennis")

session.add(category4)
session.commit()

# Create items
Item1 = Item(user_id=1, name="Tennis racquet", description="A racket or racquet is a sports implement consisting of a handled frame with an open hoop across which a network of strings or catgut is stretched tightly.",
             url="Tennis_racquet.jpg", category=category4)

session.add(Item1)
session.commit()

print "added category and items!"
