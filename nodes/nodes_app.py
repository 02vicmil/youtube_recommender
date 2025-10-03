from flask import Flask, request, jsonify, render_template, Blueprint
import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[0]))
from sqlalchemy.orm import joinedload
from tree_db_helper import init_db, Node, insert_tree, SessionLocal, create_database_if_not_exists
from chatgpt_helper import ask_chatgpt

import os
import time

def node_to_dict(node):
    """Convert a Node and its children recursively to a dictionary"""
    return {
        "id": node.id,
        "name": node.name,
        "children": [node_to_dict(child) for child in node.children]
    }

# Store last request time
last_request_time = 0

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

    @bp.route("/chat", methods=["POST"])
    def chat_with_gpt():
        global last_request_time

        # Rate limiting: 1 request per second
        now = time.time()
        if now - last_request_time < 1:
            return jsonify({"error": "Rate limit exceeded. Try again in a moment."}), 429

        data = request.json
        prompt = data.get("prompt")
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400

        last_request_time = now  # Update last request time

        # Call ChatGPT
        response = ask_chatgpt(prompt)
        return jsonify({"response": response}), 200

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
