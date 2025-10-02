from flask import Flask, request, jsonify, render_template, Blueprint
import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[0]))
from sqlalchemy.orm import joinedload
from tree_db_helper import init_db, Node, insert_tree, SessionLocal, create_database_if_not_exists
import os

def node_to_dict(node):
    """Convert a Node and its children recursively to a dictionary"""
    return {
        "id": node.id,
        "name": node.name,
        "children": [node_to_dict(child) for child in node.children]
    }


def setup_routes(app, namespace="/nodes", templates_folder=None):
    """Register all routes under a namespace."""

    templates_folder = templates_folder or os.path.join(os.path.dirname(__file__), "templates")
    bp = Blueprint("nodes", __name__, url_prefix=namespace, template_folder=templates_folder)

    create_database_if_not_exists()

    @bp.route("/")
    def index():
        return render_template('nodes/index.html')

    @bp.route(f"/tree", methods=["GET"])
    def get_tree():
        session = SessionLocal()
        root_nodes = session.query(Node).filter(Node.parent_id == None).options(joinedload(Node.children)).all()
        return jsonify([node_to_dict(node) for node in root_nodes])

    @bp.route(f"/node/<int:node_id>", methods=["GET"])
    def get_node(node_id):
        session = SessionLocal()
        node = session.query(Node).options(joinedload(Node.children)).get(node_id)
        if not node:
            return jsonify({"error": "Node not found"}), 404
        return jsonify(node_to_dict(node))

    @bp.route(f"/node", methods=["POST"])
    def add_node():
        """
        Add a subtree to a node (or as root if parent_id is None)
        JSON format:
        {
            "parent_id": 1,       # optional
            "tree": { "name": "New Node", "children": [...] }
        }
        """
        session = SessionLocal()
        data = request.json
        parent_id = data.get("parent_id")
        tree = data.get("tree")
        if not tree or "name" not in tree:
            return jsonify({"error": "Tree must have a 'name'"}), 400

        parent = session.query(Node).get(parent_id) if parent_id else None
        insert_tree(session, tree, parent=parent)
        session.commit()
        return jsonify({"message": "Node(s) added successfully"}), 201

    @bp.route(f"/node/<int:node_id>", methods=["DELETE"])
    def delete_node(node_id):
        session = SessionLocal()
        node = session.query(Node).get(node_id)
        if not node:
            return jsonify({"error": "Node not found"}), 404
        session.delete(node)
        session.commit()
        return jsonify({"message": "Node deleted successfully"}), 200

    @bp.route(f"/node/<int:node_id>", methods=["PATCH"])
    def update_node_children(node_id):
        """
        Replace all children of a node without deleting the parent.
        JSON format:
        {
            "children": [ { "name": "Child1", "children": [...] }, ... ]
        }
        """
        session = SessionLocal()
        node = session.query(Node).options(joinedload(Node.children)).get(node_id)
        if not node:
            return jsonify({"error": "Node not found"}), 404

        data = request.json
        new_children = data.get("children")
        if new_children is None:
            return jsonify({"error": "'children' key is required"}), 400

        # Delete all existing children
        for child in node.children[:]:
            session.delete(child)
        session.commit()

        # Insert new children
        for child_tree in new_children:
            insert_tree(session, child_tree, parent=node)
        session.commit()

        return jsonify({"message": "Children updated successfully"}), 200
    
    app.register_blueprint(bp)



if __name__ == "__main__":
    app = Flask(__name__)

    # Register all routes under /api namespace
    setup_routes(app)

    app.run(debug=True)
