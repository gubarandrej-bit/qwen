import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { checkService } from '../services/api';
import toast from 'react-hot-toast';
import { BookOpen, Plus, Edit, Trash2, CheckCircle, XCircle } from 'lucide-react';

const categories = [
  { value: 'PUE', label: 'ПУЭ' },
  { value: 'GOST', label: 'ГОСТ' },
  { value: 'SP', label: 'СП' },
  { value: 'FZ', label: 'ФЗ' },
  { value: 'OTHER', label: 'Другое' }
];

function NTDPage() {
  const [showAddDoc, setShowAddDoc] = useState(false);
  const [editingDoc, setEditingDoc] = useState(null);
  const [newDoc, setNewDoc] = useState({
    doc_number: '',
    doc_name: '',
    category: 'PUE',
    description: '',
    content: '',
    is_actual: true
  });

  const queryClient = useQueryClient();

  const { data: documents = [] } = useQuery({
    queryKey: ['ntd-documents'],
    queryFn: async () => {
      const response = await checkService.getNTDDocuments();
      return response.data;
    }
  });

  const addDocMutation = useMutation({
    mutationFn: async (docData) => {
      const response = await checkService.addNTDDocument(docData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['ntd-documents']);
      setShowAddDoc(false);
      setNewDoc({ doc_number: '', doc_name: '', category: 'PUE', description: '', content: '', is_actual: true });
      toast.success('Документ добавлен');
    },
    onError: () => toast.error('Ошибка добавления документа')
  });

  const updateDocMutation = useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await checkService.updateNTDDocument(id, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['ntd-documents']);
      setEditingDoc(null);
      toast.success('Документ обновлен');
    },
    onError: () => toast.error('Ошибка обновления документа')
  });

  const deleteDocMutation = useMutation({
    mutationFn: async (id) => {
      await checkService.deleteNTDDocument(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['ntd-documents']);
      toast.success('Документ удален');
    },
    onError: () => toast.error('Ошибка удаления документа')
  });

  const handleAddDoc = (e) => {
    e.preventDefault();
    addDocMutation.mutate(newDoc);
  };

  const handleUpdateDoc = (e) => {
    e.preventDefault();
    updateDocMutation.mutate({ id: editingDoc.id, data: editingDoc });
  };

  const handleDeleteDoc = (id) => {
    if (window.confirm('Вы уверены, что хотите удалить документ?')) {
      deleteDocMutation.mutate(id);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-white">База нормативно-технических документов</h2>
        <button
          onClick={() => setShowAddDoc(!showAddDoc)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
        >
          <Plus size={20} />
          Добавить документ
        </button>
      </div>

      {showAddDoc && (
        <div className="bg-dark-800 rounded-lg border border-dark-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Добавление документа НТД</h3>
          <form onSubmit={handleAddDoc} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Номер документа</label>
                <input
                  type="text"
                  value={newDoc.doc_number}
                  onChange={(e) => setNewDoc({ ...newDoc, doc_number: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  placeholder="например: ПУЭ-7"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Категория</label>
                <select
                  value={newDoc.category}
                  onChange={(e) => setNewDoc({ ...newDoc, category: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                >
                  {categories.map((cat) => (
                    <option key={cat.value} value={cat.value}>{cat.label}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Наименование</label>
              <input
                type="text"
                value={newDoc.doc_name}
                onChange={(e) => setNewDoc({ ...newDoc, doc_name: e.target.value })}
                className="w-full px-4 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                placeholder="Полное наименование документа"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Описание</label>
              <textarea
                value={newDoc.description}
                onChange={(e) => setNewDoc({ ...newDoc, description: e.target.value })}
                className="w-full px-4 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                rows={3}
                placeholder="Краткое описание документа"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_actual"
                checked={newDoc.is_actual}
                onChange={(e) => setNewDoc({ ...newDoc, is_actual: e.target.checked })}
                className="rounded bg-dark-900 border-dark-600 text-blue-600"
              />
              <label htmlFor="is_actual" className="text-dark-300">Актуальный документ</label>
            </div>
            <div className="flex gap-4 pt-4">
              <button type="submit" className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
                Добавить
              </button>
              <button
                type="button"
                onClick={() => setShowAddDoc(false)}
                className="px-6 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg"
              >
                Отмена
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Список документов */}
      <div className="grid gap-4">
        {documents.map((doc) => (
          <div key={doc.id} className="bg-dark-800 rounded-lg border border-dark-700 p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <span className={`px-2.5 py-0.5 rounded-full text-xs ${
                    doc.category === 'PUE' ? 'bg-purple-600/20 text-purple-400' :
                    doc.category === 'GOST' ? 'bg-blue-600/20 text-blue-400' :
                    doc.category === 'SP' ? 'bg-green-600/20 text-green-400' :
                    doc.category === 'FZ' ? 'bg-red-600/20 text-red-400' :
                    'bg-dark-600 text-dark-400'
                  }`}>
                    {doc.category}
                  </span>
                  {doc.is_actual ? (
                    <span className="flex items-center gap-1 text-green-400 text-xs">
                      <CheckCircle size={12} />
                      Актуальный
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-dark-500 text-xs">
                      <XCircle size={12} />
                      Неактуальный
                    </span>
                  )}
                </div>
                <h3 className="text-lg font-semibold text-white">{doc.doc_number}</h3>
                <p className="text-dark-300 mt-1">{doc.doc_name}</p>
                {doc.description && (
                  <p className="text-dark-400 text-sm mt-2">{doc.description}</p>
                )}
                <p className="text-dark-500 text-xs mt-3">
                  Добавлен: {new Date(doc.created_at).toLocaleDateString('ru-RU')}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setEditingDoc(doc)}
                  className="p-2 text-dark-400 hover:text-blue-400 hover:bg-dark-700 rounded"
                  title="Редактировать"
                >
                  <Edit size={16} />
                </button>
                <button
                  onClick={() => handleDeleteDoc(doc.id)}
                  className="p-2 text-dark-400 hover:text-red-400 hover:bg-dark-700 rounded"
                  title="Удалить"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          </div>
        ))}
        {documents.length === 0 && (
          <div className="text-center py-12 bg-dark-800 rounded-lg border border-dark-700">
            <BookOpen className="mx-auto text-dark-600 mb-4" size={48} />
            <p className="text-dark-400">Документы не найдены</p>
            <p className="text-dark-500 text-sm mt-2">Добавьте первый документ НТД</p>
          </div>
        )}
      </div>

      {/* Модальное окно редактирования */}
      {editingDoc && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-dark-800 rounded-lg border border-dark-700 max-w-2xl w-full mx-4 max-h-[80vh] overflow-auto p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Редактирование документа</h3>
            <form onSubmit={handleUpdateDoc} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">Номер документа</label>
                  <input
                    type="text"
                    value={editingDoc.doc_number}
                    onChange={(e) => setEditingDoc({ ...editingDoc, doc_number: e.target.value })}
                    className="w-full px-4 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">Категория</label>
                  <select
                    value={editingDoc.category}
                    onChange={(e) => setEditingDoc({ ...editingDoc, category: e.target.value })}
                    className="w-full px-4 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  >
                    {categories.map((cat) => (
                      <option key={cat.value} value={cat.value}>{cat.label}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Наименование</label>
                <input
                  type="text"
                  value={editingDoc.doc_name}
                  onChange={(e) => setEditingDoc({ ...editingDoc, doc_name: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Описание</label>
                <textarea
                  value={editingDoc.description || ''}
                  onChange={(e) => setEditingDoc({ ...editingDoc, description: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  rows={3}
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="edit_is_actual"
                  checked={editingDoc.is_actual}
                  onChange={(e) => setEditingDoc({ ...editingDoc, is_actual: e.target.checked })}
                  className="rounded bg-dark-900 border-dark-600 text-blue-600"
                />
                <label htmlFor="edit_is_actual" className="text-dark-300">Актуальный документ</label>
              </div>
              <div className="flex gap-4 pt-4">
                <button type="submit" className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
                  Сохранить
                </button>
                <button
                  type="button"
                  onClick={() => setEditingDoc(null)}
                  className="px-6 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg"
                >
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default NTDPage;
