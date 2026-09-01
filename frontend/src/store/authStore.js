import { create } from 'zustand';
import { authService } from '../services/api';

const useAuthStore = create((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  
  login: async (login, password) => {
    const response = await authService.login(login, password);
    const { access_token } = response.data;
    localStorage.setItem('token', access_token);
    set({ token: access_token, isAuthenticated: true });
    
    // Получаем информацию о пользователе
    const userResponse = await authService.getCurrentUser();
    set({ user: userResponse.data });
    return userResponse.data;
  },
  
  logout: () => {
    localStorage.removeItem('token');
    set({ user: null, token: null, isAuthenticated: false });
  },
  
  setUser: (user) => set({ user }),
}));

export default useAuthStore;
