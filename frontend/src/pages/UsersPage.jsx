import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userService } from '../services/api';
import toast from 'react-hot-toast';
import { Users, UserPlus, Trash2, Lock, Unlock, Edit, Shield, Key } from 'lucide-react';

function UsersPage() {
  const [showAddUser, setShowAddUser] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [selectedUserId, setSelectedUserId] = useState(null);

  const [newUser, setNewUser] = useState({
    login: '',
    password: '',
    role: 'engineer'
  });

  const queryClient = useQueryClient();

  const { data: users = [] } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await userService.getAllUsers();
      return response.data;
    }
  });

  const addUserMutation = useMutation({
    mutationFn: async (userData) => {
      const response = await userService.register(userData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['users']);
      setShowAddUser(false);
      setNewUser({ login: '', password: '', role: 'engineer' });
      toast.success('Пользователь добавлен');
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Ошибка добавления')
  });

  const deleteUserMutation = useMutation({
    mutationFn: async (userId) => {
      await userService.deleteUser(userId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['users']);
      toast.success('Пользователь удален');
    },
    onError: () => toast.error('Ошибка удаления')
  });

  const blockUserMutation = useMutation({
    mutationFn: async (userId) => {
      await userService.blockUser(userId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['users']);
      toast.success('Пользователь заблокирован');
    },
    onError: () => toast.error('Ошибка блокировки')
  });

  const unblockUserMutation = useMutation({
    mutationFn: async (userId) => {
      await userService.unblockUser(userId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['users']);
      toast.success('Пользователь разблокирован');
    },
    onError: () => toast.error('Ошибка разблокировки')
  });

  const changePasswordMutation = useMutation({
    mutationFn: async ({ userId, password }) => {
      await userService.changePassword(userId, password);
    },
    onSuccess: () => {
      setShowPasswordModal(false);
      setNewPassword('');
      setSelectedUserId(null);
      toast.success('Пароль изменен');
    },
    onError: () => toast.error('Ошибка изменения пароля')
  });

  const handleAddUser = (e) => {
    e.preventDefault();
    addUserMutation.mutate(newUser);
  };

  const handleDeleteUser = (userId) => {
    if (window.confirm('Вы уверены, что хотите удалить пользователя?')) {
      deleteUserMutation.mutate(userId);
    }
  };

  const handleBlockToggle = (user) => {
    if (user.is_blocked) {
      unblockUserMutation.mutate(user.id);
    } else {
      blockUserMutation.mutate(user.id);
    }
  };

  const handleChangePassword = (userId) => {
    setSelectedUserId(userId);
    setShowPasswordModal(true);
  };

  const handleSavePassword = () => {
    if (newPassword.length < 6) {
      toast.error('Пароль должен быть не менее 6 символов');
      return;
    }
    changePasswordMutation.mutate({ userId: selectedUserId, password: newPassword });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-white">Управление пользователями</h2>
        <button
          onClick={() => setShowAddUser(!showAddUser)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
        >
          <UserPlus size={20} />
          Добавить пользователя
        </button>
      </div>

      {showAddUser && (
        <div className="bg-dark-800 rounded-lg border border-dark-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Добавление пользователя</h3>
          <form onSubmit={handleAddUser} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Логин</label>
                <input
                  type="text"
                  value={newUser.login}
                  onChange={(e) => setNewUser({ ...newUser, login: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Пароль</label>
                <input
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  required
                  minLength={6}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Роль</label>
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="viewer">Наблюдатель</option>
                  <option value="engineer">Инженер</option>
                  <option value="admin">Администратор</option>
                </select>
              </div>
            </div>
            <div className="flex gap-4 pt-4">
              <button type="submit" className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
                Добавить
              </button>
              <button
                type="button"
                onClick={() => setShowAddUser(false)}
                className="px-6 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg"
              >
                Отмена
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Таблица пользователей */}
      <div className="bg-dark-800 rounded-lg border border-dark-700 overflow-hidden">
        <table className="w-full">
          <thead className="bg-dark-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-dark-400 uppercase tracking-wider">ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-dark-400 uppercase tracking-wider">Логин</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-dark-400 uppercase tracking-wider">Роль</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-dark-400 uppercase tracking-wider">Статус</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-dark-400 uppercase tracking-wider">Дата создания</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-dark-400 uppercase tracking-wider">Действия</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-700">
            {users.map((user) => (
              <tr key={user.id} className="hover:bg-dark-900/50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-dark-400">{user.id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-white font-medium">{user.login}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs ${
                    user.role === 'admin' ? 'bg-purple-600/20 text-purple-400' :
                    user.role === 'engineer' ? 'bg-blue-600/20 text-blue-400' :
                    'bg-dark-600 text-dark-400'
                  }`}>
                    <Shield size={12} />
                    {user.role === 'admin' ? 'Администратор' :
                     user.role === 'engineer' ? 'Инженер' : 'Наблюдатель'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${user.is_active ? 'bg-green-500' : 'bg-red-500'}`}></span>
                    <span className={user.is_active ? 'text-green-400' : 'text-red-400'}>
                      {user.is_active ? 'Активен' : 'Неактивен'}
                    </span>
                    {user.is_blocked && (
                      <span className="ml-2 px-2 py-0.5 bg-red-600/20 text-red-400 rounded text-xs">
                        Заблокирован
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-dark-400">
                  {new Date(user.created_at).toLocaleDateString('ru-RU')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => handleChangePassword(user.id)}
                      className="p-2 text-dark-400 hover:text-yellow-400 hover:bg-dark-700 rounded"
                      title="Изменить пароль"
                    >
                      <Key size={16} />
                    </button>
                    <button
                      onClick={() => handleBlockToggle(user)}
                      className={`p-2 hover:bg-dark-700 rounded ${
                        user.is_blocked ? 'text-green-400' : 'text-red-400'
                      }`}
                      title={user.is_blocked ? 'Разблокировать' : 'Заблокировать'}
                    >
                      {user.is_blocked ? <Unlock size={16} /> : <Lock size={16} />}
                    </button>
                    <button
                      onClick={() => handleDeleteUser(user.id)}
                      className="p-2 text-red-400 hover:text-red-300 hover:bg-dark-700 rounded"
                      title="Удалить"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {users.length === 0 && (
          <div className="text-center py-12">
            <Users className="mx-auto text-dark-600 mb-4" size={48} />
            <p className="text-dark-400">Пользователи не найдены</p>
          </div>
        )}
      </div>

      {/* Модальное окно изменения пароля */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-dark-800 rounded-lg border border-dark-700 max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Изменение пароля</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Новый пароль</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-4 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  placeholder="Введите новый пароль"
                  minLength={6}
                />
              </div>
              <div className="flex gap-4 pt-4">
                <button
                  onClick={handleSavePassword}
                  className="flex-1 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
                >
                  Сохранить
                </button>
                <button
                  onClick={() => {
                    setShowPasswordModal(false);
                    setNewPassword('');
                    setSelectedUserId(null);
                  }}
                  className="flex-1 px-6 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg"
                >
                  Отмена
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default UsersPage;
