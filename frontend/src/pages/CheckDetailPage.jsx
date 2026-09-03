import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { checkService, reportService } from '../services/api';
import toast from 'react-hot-toast';
import { Upload, Play, MessageSquare, FileDown, CheckCircle, XCircle, AlertCircle, Clock } from 'lucide-react';

function CheckDetailPage({ params }) {
  const checkId = params?.id || window.location.pathname.split('/').pop();
  const [files, setFiles] = useState([]);
  const [checkResults, setCheckResults] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMessages, setDialogMessages] = useState([]);

  const queryClient = useQueryClient();

  const { data: check } = useQuery({
    queryKey: ['check', checkId],
    queryFn: async () => {
      const response = await checkService.getCheck(checkId);
      return response.data;
    }
  });

  const { data: ntdDocs = [] } = useQuery({
    queryKey: ['ntd-documents'],
    queryFn: async () => {
      const response = await checkService.getNTDDocuments();
      return response.data;
    }
  });

  const uploadMutation = useMutation({
    mutationFn: async (selectedFiles) => {
      const response = await checkService.uploadFiles(checkId, selectedFiles);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['check', checkId]);
      toast.success('Файлы загружены');
      setFiles([]);
    },
    onError: () => toast.error('Ошибка загрузки файлов')
  });

  const handleFileSelect = (e) => {
    setFiles(Array.from(e.target.files));
  };

  const handleUpload = () => {
    if (files.length > 0) {
      uploadMutation.mutate(files);
    }
  };

  const runChecksMutation = useMutation({
    mutationFn: async () => {
      // Симуляция запуска проверок
      const checks = [
        { type: 'SCHEME_ELECTRIC', name: 'Проверка электрических схем' },
        { type: 'SCHEME_STRUCTURAL', name: 'Проверка структурных схем' },
        { type: 'CABLE_LENGTH', name: 'Проверка длин кабельных трасс' },
        { type: 'CABLE_JOURNAL_SPEC', name: 'Сверка кабельного журнала со спецификацией' },
        { type: 'EQUIPMENT_SPEC', name: 'Сверка оборудования со спецификацией' },
        { type: 'CABLE_SELECTION', name: 'Проверка выбора кабелей по марке и сечению' },
        { type: 'POWER_SUPPLY_CALC', name: 'Проверка расчетов источников питания' },
        { type: 'BATTERY_SELECTION', name: 'Проверка подбора аккумуляторов' },
        { type: 'NTD_COMPLIANCE', name: 'Проверка на соответствие НТД' },
        { type: 'CALCULATIONS_VERIFY', name: 'Проверка прилагаемых расчетов' }
      ];

      const messages = [];
      const results = [];

      for (const checkItem of checks) {
        messages.push({ type: 'info', text: `Запуск проверки: ${checkItem.name}` });
        setDialogMessages([...messages]);
        
        // Симуляция задержки
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Здесь должна быть реальная логика проверки через ИИ
        const result = {
          check_type: checkItem.type,
          status: 'skipped',
          severity: 'info',
          message: `Проверка не проводилась. Причина: недостаточно исходных данных для анализа.`,
          ntd_reference: '',
          details: 'Требуется загрузка соответствующих файлов документации'
        };
        
        results.push(result);
        messages.push({ 
          type: 'warning', 
          text: `${checkItem.name}: проверка не проводилась - недостаточно данных` 
        });
        setDialogMessages([...messages]);
      }

      return { results, messages };
    },
    onMutate: () => setIsRunning(true),
    onSuccess: (data) => {
      setCheckResults(data.results);
      setDialogMessages(data.messages);
      setDialogOpen(true);
      toast.success('Проверки завершены');
    },
    onError: () => toast.error('Ошибка при выполнении проверок'),
    onSettled: () => setIsRunning(false)
  });

  const handleRunChecks = () => {
    setDialogMessages([]);
    runChecksMutation.mutate();
  };

  const generateReportMutation = useMutation({
    mutationFn: async (format) => {
      const response = await reportService.generateReport(checkId, format);
      return response.data;
    },
    onSuccess: (data) => {
      toast.success(`Отчет сформирован: ${data.file_path}`);
    },
    onError: () => toast.error('Ошибка формирования отчета')
  });

  const handleGenerateReport = (format) => {
    generateReportMutation.mutate(format);
  };

  const handleGenerateCableWedomost = async () => {
    try {
      const response = await reportService.getCableWedomost(checkId);
      toast.success(`Ведомость кабеля: ${response.data.file_path}`);
    } catch {
      toast.error('Ошибка формирования ведомости кабеля');
    }
  };

  const handleGenerateEquipmentWedomost = async () => {
    try {
      const response = await reportService.getEquipmentWedomost(checkId);
      toast.success(`Ведомость оборудования: ${response.data.file_path}`);
    } catch {
      toast.error('Ошибка формирования ведомости оборудования');
    }
  };

  if (!check) {
    return <div className="text-white">Загрузка...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold text-white">{check.name}</h2>
          <p className="text-dark-400 text-sm mt-1">{check.engineering_system}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-3 py-1 rounded-full text-xs ${
            check.status === 'completed' ? 'bg-green-600/20 text-green-400' :
            check.status === 'in_progress' ? 'bg-yellow-600/20 text-yellow-400' :
            'bg-dark-600 text-dark-400'
          }`}>
            {check.status === 'completed' ? 'Завершено' :
             check.status === 'in_progress' ? 'В процессе' : 'Ожидает'}
          </span>
        </div>
      </div>

      {/* Информация о проверке */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-dark-800 rounded-lg border border-dark-700 p-4">
          <p className="text-dark-400 text-sm">Режим работы</p>
          <p className="text-white font-medium">{check.mode}</p>
        </div>
        <div className="bg-dark-800 rounded-lg border border-dark-700 p-4">
          <p className="text-dark-400 text-sm">Модель ИИ</p>
          <p className="text-white font-medium">{check.ai_model}</p>
        </div>
        <div className="bg-dark-800 rounded-lg border border-dark-700 p-4">
          <p className="text-dark-400 text-sm">Дата создания</p>
          <p className="text-white font-medium">{new Date(check.created_at).toLocaleDateString('ru-RU')}</p>
        </div>
      </div>

      {/* Загрузка файлов */}
      <div className="bg-dark-800 rounded-lg border border-dark-700 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Загрузка документов</h3>
        <div className="flex items-center gap-4">
          <input
            type="file"
            multiple
            onChange={handleFileSelect}
            className="hidden"
            id="file-upload"
            accept=".xls,.xlsx,.doc,.docx,.pdf,.dwg,.dxf"
          />
          <label
            htmlFor="file-upload"
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg cursor-pointer"
          >
            <Upload size={20} />
            Выбрать файлы
          </label>
          <button
            onClick={handleUpload}
            disabled={files.length === 0 || uploadMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg disabled:opacity-50"
          >
            <FileDown size={20} />
            Загрузить ({files.length})
          </button>
        </div>
        {files.length > 0 && (
          <div className="mt-4">
            <p className="text-dark-400 text-sm mb-2">Выбрано файлов:</p>
            <ul className="text-dark-300 text-sm">
              {files.map((f, i) => <li key={i}>{f.name}</li>)}
            </ul>
          </div>
        )}
      </div>

      {/* Запуск проверок */}
      <div className="bg-dark-800 rounded-lg border border-dark-700 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Выполнение проверок</h3>
        <div className="flex items-center gap-4">
          <button
            onClick={handleRunChecks}
            disabled={isRunning}
            className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50"
          >
            <Play size={20} />
            {isRunning ? 'Выполнение...' : 'Запустить проверки'}
          </button>
        </div>

        {/* Список проверок */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-3">
          {[
            { type: 'SCHEME_ELECTRIC', name: 'Проверка электрических схем' },
            { type: 'SCHEME_STRUCTURAL', name: 'Проверка структурных схем' },
            { type: 'CABLE_LENGTH', name: 'Проверка длин кабельных трасс' },
            { type: 'CABLE_JOURNAL_SPEC', name: 'Сверка кабельного журнала со спецификацией' },
            { type: 'EQUIPMENT_SPEC', name: 'Сверка оборудования со спецификацией' },
            { type: 'CABLE_SELECTION', name: 'Проверка выбора кабелей' },
            { type: 'POWER_SUPPLY_CALC', name: 'Проверка расчетов ИП' },
            { type: 'BATTERY_SELECTION', name: 'Проверка подбора АКБ' },
            { type: 'NTD_COMPLIANCE', name: 'Проверка на соответствие НТД' },
            { type: 'CALCULATIONS_VERIFY', name: 'Проверка расчетов' }
          ].map((item) => {
            const result = checkResults.find(r => r.check_type === item.type);
            return (
              <div key={item.type} className="flex items-center gap-3 p-3 bg-dark-900 rounded-lg border border-dark-700">
                {result?.status === 'passed' ? <CheckCircle size={18} className="text-green-500" /> :
                 result?.status === 'failed' ? <XCircle size={18} className="text-red-500" /> :
                 result?.status === 'skipped' ? <AlertCircle size={18} className="text-yellow-500" /> :
                 <Clock size={18} className="text-dark-500" />}
                <span className="text-dark-300 text-sm">{item.name}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Генерация отчетов */}
      <div className="bg-dark-800 rounded-lg border border-dark-700 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Генерация отчетов</h3>
        <div className="flex flex-wrap gap-4">
          <button
            onClick={() => handleGenerateReport('doc')}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
          >
            <FileDown size={20} />
            Отчет DOC
          </button>
          <button
            onClick={() => handleGenerateReport('xls')}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg"
          >
            <FileDown size={20} />
            Отчет XLS
          </button>
          <button
            onClick={handleGenerateCableWedomost}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
          >
            <FileDown size={20} />
            Ведомость кабеля
          </button>
          <button
            onClick={handleGenerateEquipmentWedomost}
            className="flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg"
          >
            <FileDown size={20} />
            Ведомость оборудования
          </button>
        </div>
      </div>

      {/* Диалоговое окно результатов */}
      {dialogOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-dark-800 rounded-lg border border-dark-700 max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden flex flex-col">
            <div className="p-4 border-b border-dark-700 flex justify-between items-center">
              <h3 className="text-lg font-semibold text-white">Результаты проверок</h3>
              <button onClick={() => setDialogOpen(false)} className="text-dark-400 hover:text-white">
                <XCircle size={24} />
              </button>
            </div>
            <div className="p-4 overflow-auto flex-1">
              <div className="space-y-2">
                {dialogMessages.map((msg, i) => (
                  <div key={i} className={`p-3 rounded-lg ${
                    msg.type === 'info' ? 'bg-blue-900/30 text-blue-200' :
                    msg.type === 'warning' ? 'bg-yellow-900/30 text-yellow-200' :
                    msg.type === 'error' ? 'bg-red-900/30 text-red-200' :
                    'bg-dark-900 text-dark-300'
                  }`}>
                    <div className="flex items-start gap-2">
                      {msg.type === 'info' ? <MessageSquare size={16} className="mt-0.5" /> :
                       msg.type === 'warning' ? <AlertCircle size={16} className="mt-0.5" /> :
                       <XCircle size={16} className="mt-0.5" />}
                      <span className="text-sm">{msg.text}</span>
                    </div>
                  </div>
                ))}
                {dialogMessages.length === 0 && (
                  <p className="text-dark-400 text-center py-8">Нет сообщений</p>
                )}
              </div>
              
              {/* Результаты проверок */}
              {checkResults.length > 0 && (
                <div className="mt-6">
                  <h4 className="text-white font-medium mb-3">Детали проверок:</h4>
                  <div className="space-y-2">
                    {checkResults.map((result, i) => (
                      <div key={i} className="p-3 bg-dark-900 rounded-lg border border-dark-700">
                        <div className="flex items-center gap-2 mb-2">
                          {result.status === 'passed' ? <CheckCircle size={16} className="text-green-500" /> :
                           result.status === 'failed' ? <XCircle size={16} className="text-red-500" /> :
                           <AlertCircle size={16} className="text-yellow-500" />}
                          <span className="text-white font-medium text-sm">{result.check_type}</span>
                        </div>
                        <p className="text-dark-300 text-sm">{result.message}</p>
                        {result.ntd_reference && (
                          <p className="text-dark-500 text-xs mt-1">НТД: {result.ntd_reference}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="p-4 border-t border-dark-700 flex justify-end">
              <button
                onClick={() => setDialogOpen(false)}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default CheckDetailPage;
