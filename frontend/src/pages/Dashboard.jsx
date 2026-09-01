import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { checkService } from '../services/api';
import { FileCheck, AlertCircle, CheckCircle, Clock, TrendingUp } from 'lucide-react';

function Dashboard() {
  const [stats, setStats] = useState({
    total: 0,
    completed: 0,
    inProgress: 0,
    critical: 0
  });

  const { data: checks = [] } = useQuery({
    queryKey: ['checks'],
    queryFn: async () => {
      const response = await checkService.getChecks();
      return response.data;
    }
  });

  useEffect(() => {
    if (checks) {
      setStats({
        total: checks.length,
        completed: checks.filter(c => c.status === 'completed').length,
        inProgress: checks.filter(c => c.status === 'in_progress').length,
        pending: checks.filter(c => c.status === 'pending').length
      });
    }
  }, [checks]);

  const statCards = [
    { title: 'Всего проверок', value: stats.total, icon: FileCheck, color: 'blue' },
    { title: 'Завершено', value: stats.completed, icon: CheckCircle, color: 'green' },
    { title: 'В процессе', value: stats.inProgress, icon: Clock, color: 'yellow' },
    { title: 'Ожидает', value: stats.pending || 0, icon: AlertCircle, color: 'orange' }
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.title} className="bg-dark-800 rounded-lg p-6 border border-dark-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-dark-400 text-sm">{stat.title}</p>
                  <p className="text-3xl font-bold text-white mt-2">{stat.value}</p>
                </div>
                <div className={`p-3 bg-${stat.color}-600/20 rounded-lg`}>
                  <Icon className={`text-${stat.color}-500`} size={24} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="bg-dark-800 rounded-lg border border-dark-700 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Последние проверки</h3>
        {checks.length > 0 ? (
          <div className="space-y-3">
            {checks.slice(0, 5).map((check) => (
              <div key={check.id} className="flex items-center justify-between p-4 bg-dark-900 rounded-lg border border-dark-700">
                <div>
                  <p className="text-white font-medium">{check.name}</p>
                  <p className="text-dark-500 text-sm">{check.engineering_system}</p>
                </div>
                <div className="flex items-center gap-4">
                  <span className={`px-3 py-1 rounded-full text-xs ${
                    check.status === 'completed' ? 'bg-green-600/20 text-green-400' :
                    check.status === 'in_progress' ? 'bg-yellow-600/20 text-yellow-400' :
                    'bg-dark-600 text-dark-400'
                  }`}>
                    {check.status === 'completed' ? 'Завершено' :
                     check.status === 'in_progress' ? 'В процессе' : 'Ожидает'}
                  </span>
                  <span className="text-dark-500 text-sm">
                    {new Date(check.created_at).toLocaleDateString('ru-RU')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <FileCheck className="mx-auto text-dark-600 mb-4" size={48} />
            <p className="text-dark-400">Проверки еще не созданы</p>
            <p className="text-dark-500 text-sm mt-2">Создайте новую проверку для начала работы</p>
          </div>
        )}
      </div>

      <div className="bg-dark-800 rounded-lg border border-dark-700 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Поддерживаемые системы</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {[
            'Электроснабжение', 'Электроосвещение', 'Пожарная сигнализация',
            'СОУЭ', 'Пожаротушение', 'СКС', 'ЛВС', 'ВОЛС',
            'Видеонаблюдение', 'СКУД', 'Охранная сигнализация', 'АСУ/АСУТП'
          ].map((system) => (
            <div key={system} className="flex items-center gap-2 p-3 bg-dark-900 rounded-lg border border-dark-700">
              <CheckCircle size={16} className="text-blue-500" />
              <span className="text-dark-300 text-sm">{system}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
