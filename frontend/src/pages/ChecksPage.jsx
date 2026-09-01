import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { checkService } from '../services/api';
import toast from 'react-hot-toast';
import { Plus, Upload, Play, FileText, Trash2 } from 'lucide-react';

const engineeringSystems = [
  { value: 'electrosnabzhenie', label: 'Электроснабжение' },
  { value: 'electroosveshchenie', label: 'Электроосвещение' },
  { value: 'pozarnaya_signalizatsiya', label: 'Пожарная сигнализация' },
  { value: 'SOUE', label: 'СОУЭ' },
  { value: 'pozharotushenie', label: 'Пожаротушение' },
  { value: 'SKS', label: 'СКС' },
  { value: 'LVS', label: 'ЛВС' },
  { value: 'VOLS', label: 'ВОЛС' },
  { value: 'videonablyudenie', label: 'Видеонаблюдение' },
  { value: 'SKUD', label: 'СКУД' },
  { value: 'okhrannaya_signalizatsiya', label: 'Охранная сигнализация' },
  { value: 'ASU', label: 'АСУ' },
  { value: 'ASUTP', label: 'АСУТП' }
];

const aiModels = [
  { value: 'Qwen-2.5-1.5B', label: 'Qwen-2.5-1.5B (Локальная)' },
  { value: 'Mistral-7B-Instruct', label: 'Mistral-7B (Облачная)' },
  { value: 'Phi-2', label: 'Phi-2 (Облачная)' }
];

function ChecksPage() {
  const [showNewCheck, setShowNewCheck] = useState(false);
  const [newCheck, setNewCheck] = useState({
    name: '',
    engineering_system: 'electrosnabzhenie',
    mode: 'local',
    ai_model: 'Qwen-2.5-1.5B'
  });

  const queryClient = useQueryClient();

  const { data: checks = [] } = useQuery({
    queryKey: ['checks'],
    queryFn: async () => {
      const response = await checkService.getChecks();
      return response.data;
    }
  });

  const createCheckMutation = useMutation({
    mutationFn: async (data) => {
      const response = await checkService.createCheck(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['checks']);
      setShowNewCheck(false);
      setNewCheck({ name: '', engineering_system: 'electrosnabzhenie', mode: 'local', ai_model: 'Qwen-2.5-1.5B' });
      toast.success('Проверка создана');
    },
    onError: () => toast.error('Ошибка создания проверки')
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    createCheckMutation.mutate(newCheck);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-white">Проверки документации</h2>
        <button
          onClick={() => setShowNewCheck(!showNewCheck)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
        >
          <Plus size={20} />
          Новая проверка
        </button>
      </div>

      {showNewCheck && (
        <div className="bg-dark-800 rounded-lg border border-dark-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Создание новой проверки</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Наименование проверки</label>
              <input
                type="text"
                value={newCheck.name}
                onChange={(e) => setNewCheck({ ...newCheck, name: e.target.value })}
                className="w-full px-4 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                required
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Инженерная система</label>
                <select
                  value={newCheck.engineering_system}
                  onChange={(e) => setNewCheck({ ...newCheck, engineering_system: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                >
                  {engineeringSystems.map((sys) => (
                    <option key={sys.value} value={sys.value}>{sys.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Режим работы</label>
                <select
                  value={newCheck.mode}
                  onChange={(e) => setNewCheck({ ...newCheck, mode: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="local">Локальный</option>
                  <option value="cloud">Облачный</option>
                  <option value="hybrid">Гибридный</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Модель ИИ</label>
                <select
                  value={newCheck.ai_model}
                  onChange={(e) => setNewCheck({ ...newCheck, ai_model: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                >
                  {aiModels.map((model) => (
                    <option key={model.value} value={model.value}>{model.label}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex gap-4 pt-4">
              <button type="submit" className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
                Создать
              </button>
              <button type="button" onClick={() => setShowNewCheck(false)} className="px-6 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg">
                Отмена
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="grid gap-4">
        {checks.map((check) => (
          <div key={check.id} className="bg-dark-800 rounded-lg border border-dark-700 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-white">{check.name}</h3>
                <p className="text-dark-400 text-sm mt-1">{check.engineering_system}</p>
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
                <a href={`/checks/${check.id}`} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm">
                  Открыть
                </a>
              </div>
            </div>
          </div>
        ))}
        {checks.length === 0 && (
          <div className="text-center py-12 bg-dark-800 rounded-lg border border-dark-700">
            <FileText className="mx-auto text-dark-600 mb-4" size={48} />
            <p className="text-dark-400">Проверки еще не созданы</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default ChecksPage;
