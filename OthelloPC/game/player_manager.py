"""
玩家管理器 - 无密码轻量级版本
用于闯关/计时模式的玩家身份管理
"""

import json
import os
from datetime import datetime
from typing import List, Optional


class PlayerManager:
    """
    玩家管理器 - 负责玩家选择、记录和命名策略

    功能：
    1. 选择或创建玩家（无密码）
    2. 管理最近使用的玩家列表
    3. 根据游戏模式自动决定显示名称
    """

    def __init__(self, data_file: str = None):
        """初始化玩家管理器"""
        if data_file is None:
            # 默认数据文件路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(os.path.dirname(current_dir), 'data')
            os.makedirs(data_dir, exist_ok=True)
            data_file = os.path.join(data_dir, 'players.json')

        self.data_file = data_file
        self.current_player: Optional[str] = None
        self._data = self._load_data()

    def _load_data(self) -> dict:
        """加载玩家数据"""
        if not os.path.exists(self.data_file):
            return {
                "version": "1.0",
                "users": [],
                "current_user": None,
                "recent_users": []
            }

        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 兼容性检查
                if "users" not in data:
                    data["users"] = []
                if "recent_users" not in data:
                    data["recent_users"] = []
                return data
        except Exception as e:
            print(f"加载玩家数据失败: {e}")
            return {
                "version": "1.0",
                "users": [],
                "current_user": None,
                "recent_users": []
            }

    def _save_data(self):
        """保存玩家数据"""
        try:
            self._data["current_user"] = self.current_player
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存玩家数据失败: {e}")

    def select_player(self, username: str) -> bool:
        """
        选择或创建玩家

        Args:
            username: 玩家用户名

        Returns:
            bool: 成功返回True
        """
        if not username or not username.strip():
            return False

        username = username.strip()

        # 检查是否是新用户
        user_exists = False
        for user in self._data["users"]:
            if user["username"] == username:
                # 更新最后使用时间
                user["last_used"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                user["total_games"] = user.get("total_games", 0) + 1
                user_exists = True
                break

        # 创建新用户
        if not user_exists:
            new_user = {
                "username": username,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_used": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_games": 0,
                "favorite_mode": None
            }
            self._data["users"].append(new_user)

        # 更新当前玩家
        self.current_player = username

        # 更新最近使用列表
        self._update_recent_users(username)

        # 保存数据
        self._save_data()

        return True

    def _update_recent_users(self, username: str):
        """更新最近使用的玩家列表"""
        recent = self._data.get("recent_users", [])

        # 移除旧的相同用户名
        if username in recent:
            recent.remove(username)

        # 添加到列表开头
        recent.insert(0, username)

        # 限制列表长度为10
        self._data["recent_users"] = recent[:10]

    def logout(self):
        """登出当前玩家"""
        self.current_player = None
        self._data["current_user"] = None
        self._save_data()

    def get_recent_players(self) -> List[str]:
        """获取最近使用的玩家列表"""
        return self._data.get("recent_users", [])

    @property
    def is_logged_in(self) -> bool:
        """检查是否有玩家登录"""
        return self.current_player is not None

    def get_display_name(self, game_mode: str, winner: str = None) -> str:
        """
        根据游戏模式和赢家返回应该显示的玩家名称

        Args:
            game_mode: 游戏模式 ('normal', 'challenge', 'timed', 'cheat')
            winner: 赢家 ('black', 'white', 'draw')，仅普通模式需要

        Returns:
            str: 玩家显示名称
        """
        if game_mode in ['challenge', 'timed']:
            # 闯关/计时模式：返回登录用户名
            if self.is_logged_in:
                return self.current_player
            else:
                return "未登录"

        elif game_mode == 'normal':
            # 普通模式：根据赢家返回固定名称
            if winner == 'black':
                return "玩家1"
            elif winner == 'white':
                return "玩家2"
            elif winner == 'draw':
                return "平局"
            else:
                return "未知"

        else:
            # 作弊模式或其他：返回通用名称
            return "玩家1"

    def get_player_info(self, username: str) -> Optional[dict]:
        """获取指定玩家的信息"""
        for user in self._data["users"]:
            if user["username"] == username:
                return user
        return None

    def get_all_players(self) -> List[str]:
        """获取所有玩家用户名列表"""
        return [user["username"] for user in self._data["users"]]

    def update_favorite_mode(self, mode: str):
        """更新当前玩家的偏好模式"""
        if not self.is_logged_in:
            return

        for user in self._data["users"]:
            if user["username"] == self.current_player:
                user["favorite_mode"] = mode
                self._save_data()
                break


# 全局单例
_player_manager_instance: Optional[PlayerManager] = None


def get_player_manager() -> PlayerManager:
    """获取玩家管理器单例"""
    global _player_manager_instance
    if _player_manager_instance is None:
        _player_manager_instance = PlayerManager()
    return _player_manager_instance


def init_player_manager(data_file: str = None) -> PlayerManager:
    """初始化玩家管理器（可指定数据文件路径）"""
    global _player_manager_instance
    _player_manager_instance = PlayerManager(data_file)
    return _player_manager_instance
