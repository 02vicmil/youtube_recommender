# db_helper.py
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

import pathlib
import os

def get_directory_path(__file__in, up_directories=0):
    return str(pathlib.Path(__file__in).parents[up_directories].resolve()).replace("\\", "/")

# -----------------------------
# Database setup
# -----------------------------
BASE_DIR = get_directory_path(__file__, 0)  # adjust up_directories if needed
DB_FILE = os.path.join(BASE_DIR, "nodes.db")
DB_PATH = f"sqlite:///{DB_FILE}"

engine = create_engine(DB_PATH, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Node(Base):
    __tablename__ = 'nodes'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey('nodes.id'), nullable=True)
    
    # Self-referential relationship
    children = relationship(
        "Node",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    parent = relationship(
        "Node",
        back_populates="children",
        remote_side=[id]
    )

    __table_args__ = (
        UniqueConstraint('name', 'parent_id', name='_name_parent_uc'),
    )

    def __repr__(self):
        return f"<Node(id={self.id}, name='{self.name}', parent_id={self.parent_id})>"

def init_db(engine):
    Base.metadata.create_all(engine)

# Recursive helper to insert nodes from a dictionary
def insert_tree(session, tree, parent=None):
    """
    Inserts nodes recursively from a nested dictionary.
    If a node with the same name under the same parent exists, it reuses it.
    
    Example tree format:
    {
        "name": "root",
        "children": [
            {"name": "child1"},
            {"name": "child2", "children": [{"name": "grandchild1"}]}
        ]
    }
    """
    parent_id = parent.id if parent else None

    # Check if node already exists
    node = session.query(Node).filter_by(name=tree['name'], parent_id=parent_id).first()
    
    if not node:
        node = Node(name=tree['name'], parent=parent)
        session.add(node)
        session.flush()  # assign id
    
    # Recurse for children
    for child in tree.get('children', []):
        insert_tree(session=session, tree=child, parent=node)
    
    return node


def create_database_if_not_exists():
    # Create tables if they don't exist
    init_db(engine=engine)

    session = SessionLocal()

    # Only insert tree if the table is empty
    if session.query(Node).count() == 0:
        knowledge_tree = {
            "name": "root",
            "children": [
                {
                    "name": "Science",
                    "children": [
                        {"name": "Physics", "children": [
                            {"name": "Mechanics"},
                            {"name": "Thermodynamics"}
                        ]},
                        {"name": "Chemistry", "children": [
                            {"name": "Organic Chemistry"},
                            {"name": "Inorganic Chemistry"}
                        ]},
                        {"name": "Biology", "children": [
                            {"name": "Genetics"},
                            {"name": "Ecology"}
                        ]}
                    ]
                },
                {
                    "name": "Arts",
                    "children": [
                        {"name": "Music"},
                        {"name": "Painting"},
                        {"name": "Literature"}
                    ]
                },
                {
                    "name": "Technology",
                    "children": [
                        {"name": "Computer Science"},
                        {"name": "Electronics"},
                        {"name": "Robotics"}
                    ]
                }
            ]
        }
        insert_tree(tree=knowledge_tree, session=session)
        session.commit()

    # Print all nodes
    for node in session.query(Node).all():
        print(node)


# Example usage
if __name__ == "__main__":
    create_database_if_not_exists()
