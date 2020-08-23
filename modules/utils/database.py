from sqlalchemy import BigInteger, Column, String, create_engine, literal
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine('sqlite:///guilds.db', echo=False)
Base = declarative_base()

class GuildPrefix(Base):
    __tablename__ = 'prefixes'

    guild_id = Column(BigInteger, primary_key=True)
    guild_prefix = Column(String)

    def __repr__(self):
        return f"Prefix({self.guild_prefix})"

class StreamNotifications(Base):
    __tablename__ = 'streamNotificationsSettings'

    guild_id = Column(BigInteger, primary_key=True)
    notifications_usernames = Column(String)
    notifications_channel_id = Column(BigInteger)
    notifications_custom_text = Column(String)
    notifications_keywords = Column(String)

    def __repr__(self):
        return f"StreamNotifications({self.guild_id})"

# Create Databases
Base.metadata.create_all(engine)

# Start Database Session
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)
main_session = Session()

def get_db_session():
    return main_session

def generate_db_session():
    return Session()
