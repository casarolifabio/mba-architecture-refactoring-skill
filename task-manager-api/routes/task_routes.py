from flask import Blueprint, request, jsonify
from controllers import task_controller

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    data, status = task_controller.list_tasks()
    return jsonify(data), status


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    data, status = task_controller.get_task(task_id)
    return jsonify(data), status


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data, status = task_controller.create_task(request.get_json())
    return jsonify(data), status


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data, status = task_controller.update_task(task_id, request.get_json())
    return jsonify(data), status


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    data, status = task_controller.delete_task(task_id)
    return jsonify(data), status


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    data, status = task_controller.search_tasks(
        q=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=request.args.get('priority', ''),
        user_id=request.args.get('user_id', ''),
    )
    return jsonify(data), status


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    data, status = task_controller.task_stats()
    return jsonify(data), status
