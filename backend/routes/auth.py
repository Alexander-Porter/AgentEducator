from flask import Blueprint, request, jsonify
from models.user import User
from utils.jwt_util import generate_token
from utils.db_util import get_user_by_credentials

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'message': '用户名和密码不能为空'}), 400

        user = get_user_by_credentials(username, password)
        if not user:
            return jsonify({'message': '用户名或密码错误'}), 401

        # 如果验证通过，生成 JWT 令牌
        token = generate_token(str(user.id))  # 确保 UUID 转换为字符串

        return jsonify({
            'id': user.id,
            'name': user.name,
            'role': user.role,
            'token': token
        }), 200
    except Exception as e:
        return jsonify({'message': f'登录失败: {str(e)}'}), 500