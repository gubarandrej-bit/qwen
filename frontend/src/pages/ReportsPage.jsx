import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { checkService, reportService } from '../services/api';
import toast from 'react-hot-toast';
import { FileText, Download, Calendar, User } from 'lucide-react';

function ReportsPage() {
  const [selectedCheck, setSelectedCheck] = useState(null);
  const [reportFormat, setReportFormat] = useState('doc');

  const { data: checks = [] } = useQuery({
    queryKey: ['checks'],
    queryFn: async () => {
      const response = await checkService.getChecks();
      return response.data;
    }
  });

  const completedChecks = checks.filter(c => c.status === 'completed');

  const handleGenerateReport = async () => {
    if (!selectedCheck) {
      toast.error('Выберите проверку для формирования отчета');
      return;
    }

    try {
      const response = await reportService.generateReport(selectedCheck, reportFormat);
      toast.success(`Отчет сформирован: ${response.data.file_path}`);
    } catch {
      toast.error('Ошибка формирования отчета');
    }
  };

  const handleGenerateCableWedomost = async (checkId) => {
    try {
      const response = await reportService.getCableWedomost(checkId);
      toast.success(`Ведомость кабеля: ${response.data.file_path}`);
    } catch {
      toast.error('Ошибка формирования ведомости кабеля');
    }
  };

  const handleGenerateEquipmentWedomost = async (checkId) => {
    try {
      const response = await reportService.getEquipmentWedomost(checkId);
      toast.success(`Ведомость оборудования: ${response.data.file_path}`);
    } catch {
      toast.error('Ошибка формирования ведомости оборудования');
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-white">Отчеты и ведомости</h2>

      {/* Генерация отчета */}
      <div className="bg-dark-800 rounded-lg border border-dark-700 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Формирование отчета о проверке</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-dark-300 mb-2">Выберите проверку</label>
            <select
              value={selectedCheck || ''}
              onChange={(e) => setSelectedCheck(e.target.value ? parseInt(e.target.value) : null)}
              className="w-full px-4 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
            >
              <option value="">-- Выберите проверку --</option>
              {completedChecks.map((check) => (
                <option key={check.id} value={check.id}>
                  {check.name} ({check.engineering_system})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-dark-300 mb-2">Формат отчета</label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  name="format"
                  value="doc"
                  checked={reportFormat === 'doc'}
                  onChange={(e) => setReportFormat(e.target.value)}
                  className="text-blue-600"
                />
                <span className="text-dark-300">DOC (Word)</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  name="format"
                  value="xls"
                  checked={reportFormat === 'xls'}
                  onChange={(e) => setReportFormat(e.target.value)}
                  className="text-blue-600"
                />
                <span className="text-dark-300">XLS (Excel)</span>
              </label>
            </div>
          </div>
          <button
            onClick={handleGenerateReport}
            disabled={!selectedCheck}
            className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download size={20} />
            Сформировать отчет
          </button>
        </div>
      </div>

      {/* Список проверок для быстрого доступа к ведомостям */}
      <div className="bg-dark-800 rounded-lg border border-dark-700 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Доступные проверки</h3>
        <div className="grid gap-4">
          {checks.map((check) => (
            <div key={check.id} className="p-4 bg-dark-900 rounded-lg border border-dark-700">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <FileText className="text-blue-500" size={20} />
                    <h4 className="text-white font-medium">{check.name}</h4>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-dark-400">
                    <span className="flex items-center gap-1">
                      <User size={14} />
                      {check.engineering_system}
                    </span>
                    <span className="flex items-center gap-1">
                      <Calendar size={14} />
                      {new Date(check.created_at).toLocaleDateString('ru-RU')}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      check.status === 'completed' ? 'bg-green-600/20 text-green-400' :
                      check.status === 'in_progress' ? 'bg-yellow-600/20 text-yellow-400' :
                      'bg-dark-600 text-dark-400'
                    }`}>
                      {check.status === 'completed' ? 'Завершено' :
                       check.status === 'in_progress' ? 'В процессе' : 'Ожидает'}
                    </span>
                  </div>
                </div>
                {check.status === 'completed' && (
                  <div className="flex flex-col gap-2">
                    <button
                      onClick={() => handleGenerateCableWedomost(check.id)}
                      className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded"
                    >
                      Ведомость кабеля
                    </button>
                    <button
                      onClick={() => handleGenerateEquipmentWedomost(check.id)}
                      className="px-3 py-1.5 bg-orange-600 hover:bg-orange-700 text-white text-sm rounded"
                    >
                      Ведомость оборудования
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
          {checks.length === 0 && (
            <div className="text-center py-12">
              <FileText className="mx-auto text-dark-600 mb-4" size={48} />
              <p className="text-dark-400">Проверки не найдены</p>
              <p className="text-dark-500 text-sm mt-2">Создайте новую проверку для начала работы</p>
            </div>
          )}
        </div>
      </div>

      {/* Информация о форматах отчетов */}
      <div className="bg-dark-800 rounded-lg border border-dark-700 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Информация об отчетах</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-dark-900 rounded-lg border border-dark-700">
            <h4 className="text-white font-medium mb-2">Отчет DOC</h4>
            <p className="text-dark-400 text-sm">
              Содержит полную информацию о проверке: общие данные, критические и некритические замечания, 
              ссылки на НТД, выводы. Форматируется в виде документа Word с заголовками и таблицами.
            </p>
          </div>
          <div className="p-4 bg-dark-900 rounded-lg border border-dark-700">
            <h4 className="text-white font-medium mb-2">Отчет XLS</h4>
            <p className="text-dark-400 text-sm">
              Табличный формат с подробной статистикой: все замечания по типам, статусам проверок, 
              количество критических и некритических ошибок. Удобно для дальнейшей обработки.
            </p>
          </div>
          <div className="p-4 bg-dark-900 rounded-lg border border-dark-700">
            <h4 className="text-white font-medium mb-2">Ведомость кабеля</h4>
            <p className="text-dark-400 text-sm">
              Таблица со списком всех кабелей: марка, количество, длина, трасса прокладки. 
              Включает итоговую сумму длин всех кабелей.
            </p>
          </div>
          <div className="p-4 bg-dark-900 rounded-lg border border-dark-700">
            <h4 className="text-white font-medium mb-2">Ведомость оборудования</h4>
            <p className="text-dark-400 text-sm">
              Полный список оборудования и материалов: наименование, тип, количество, единицы измерения. 
              Сверяется со спецификацией проекта.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ReportsPage;
