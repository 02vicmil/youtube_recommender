from flask import Flask, request, jsonify, render_template

from youtube_recommend import search_app
from nodes import nodes_app

if __name__ == "__main__":
    app = Flask(__name__)

    search_app.setup_routes(app)
    nodes_app.setup_routes(app)

    app.run(debug=True, port=5005)
