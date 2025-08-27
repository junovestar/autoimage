import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Home, 
  Settings, 
  Plus,
  Trash2,
  Download,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  Upload,
  Image,
  Play,
  RefreshCw,
  Eye,
  X
} from 'lucide-react';
import './App.css';

function App() {
  // States
  const [apiKeys, setApiKeys] = useState([]);
  const [newApiKey, setNewApiKey] = useState('');
  const [tasks, setTasks] = useState([]);
  const [prompts, setPrompts] = useState(['']);
  const [batchName, setBatchName] = useState('Batch 1');
  const [status, setStatus] = useState({});
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('home');
  const [selectedImage, setSelectedImage] = useState(null);
  const [uploadedImagePath, setUploadedImagePath] = useState('');
  const [uploadStatus, setUploadStatus] = useState('');
  const [selectedTask, setSelectedTask] = useState(null);
  const [notification, setNotification] = useState(null);
  const [bulkText, setBulkText] = useState('');
  const [useAI, setUseAI] = useState(true);
  const [processingPrompts, setProcessingPrompts] = useState(false);
  
  // Character sync states
  const [characterSync, setCharacterSync] = useState(false);
  const [characterAnalysis, setCharacterAnalysis] = useState('');
  const [analyzingCharacter, setAnalyzingCharacter] = useState(false);

  // Load data on mount
  useEffect(() => {
    loadApiKeys();
    loadTasks();
    loadStatus();
    
    // Auto refresh every 10 seconds
    const interval = setInterval(() => {
      loadTasks();
      loadStatus();
    }, 10000);
    
    return () => clearInterval(interval);
  }, []);

  // Custom notification system
  const showNotification = (message, type = 'success') => {
    setNotification({ message, type, id: Date.now() });
    setTimeout(() => {
      setNotification(null);
    }, 4000);
  };

  // API functions
  const loadApiKeys = async () => {
    try {
      const response = await axios.get('/api/keys');
      setApiKeys(response.data.keys);
    } catch (error) {
      showNotification('Lỗi khi tải API keys: ' + getErrorMessage(error), 'error');
    }
  };

  const loadTasks = async () => {
    try {
      const response = await axios.get('/api/tasks');
      setTasks(response.data.tasks);
    } catch (error) {
      showNotification('Lỗi khi tải danh sách tasks: ' + getErrorMessage(error), 'error');
    }
  };

  const loadStatus = async () => {
    try {
      const response = await axios.get('/api/status');
      setStatus(response.data);
    } catch (error) {
      showNotification('Lỗi khi tải trạng thái hệ thống: ' + getErrorMessage(error), 'error');
    }
  };

  // Error handling in Vietnamese
  const getErrorMessage = (error) => {
    if (error.response?.data?.error) {
      const errorMsg = error.response.data.error;
      // Translate common errors
      if (errorMsg.includes('RESOURCE_EXHAUSTED')) {
        return 'API key đã hết quota, vui lòng thêm key mới hoặc chờ reset quota';
      }
      if (errorMsg.includes('INVALID_ARGUMENT')) {
        return 'Prompt không hợp lệ, vui lòng thử lại';
      }
      if (errorMsg.includes('PERMISSION_DENIED')) {
        return 'API key không có quyền truy cập hoặc không hợp lệ';
      }
      if (errorMsg.includes('UNAVAILABLE')) {
        return 'Dịch vụ Gemini tạm thời không khả dụng';
      }
      return errorMsg;
    }
    if (error.message.includes('Network Error')) {
      return 'Không thể kết nối đến server, vui lòng kiểm tra kết nối';
    }
    return error.message || 'Lỗi không xác định';
  };

  const addApiKey = async () => {
    if (!newApiKey.trim()) {
      showNotification('Vui lòng nhập API key', 'warning');
      return;
    }
    
    setLoading(true);
    try {
      await axios.post('/api/keys', { key: newApiKey.trim() });
      setNewApiKey('');
      loadApiKeys();
      loadStatus();
      showNotification('Thêm API key thành công!', 'success');
    } catch (error) {
      showNotification('Lỗi khi thêm API key: ' + getErrorMessage(error), 'error');
    } finally {
      setLoading(false);
    }
  };

  const removeApiKey = async (keySuffix) => {
    try {
      await axios.delete(`/api/keys/${keySuffix}`);
      loadApiKeys();
      loadStatus();
      showNotification('Xóa API key thành công!', 'success');
    } catch (error) {
      showNotification('Lỗi khi xóa API key: ' + getErrorMessage(error), 'error');
    }
  };

  const createBatchTask = async () => {
    const validPrompts = prompts.filter(p => p.trim());
    if (validPrompts.length === 0) {
      showNotification('Vui lòng nhập ít nhất một prompt', 'warning');
      return;
    }

    if (apiKeys.length === 0) {
      showNotification('Vui lòng thêm ít nhất một API key', 'warning');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/tasks', {
        prompts: validPrompts,
        name: batchName,
        input_image_path: uploadedImagePath || null,
        character_sync: characterSync,
        character_analysis: characterAnalysis || null,
        auto_start: true  // Mặc định tự động chạy
      });
      
      setPrompts(['']);
      setBatchName(`Batch ${tasks.length + 2}`);
      setSelectedImage(null);
      setUploadedImagePath('');
      setUploadStatus('');
      setCharacterSync(false);
      setCharacterAnalysis('');
      loadTasks();
      loadStatus();
      showNotification(response.data.message, 'success');
    } catch (error) {
      showNotification('Lỗi khi tạo task: ' + getErrorMessage(error), 'error');
    } finally {
      setLoading(false);
    }
  };

  const startTaskManual = async (taskId) => {
    try {
      const response = await axios.post(`/api/tasks/${taskId}/start`);
      loadTasks();
      loadStatus();
      showNotification(response.data.message, 'success');
    } catch (error) {
      showNotification('Lỗi khi chạy task: ' + getErrorMessage(error), 'error');
    }
  };

  const addToQueue = async (taskId) => {
    try {
      await axios.post(`/api/queue/add/${taskId}`);
      loadTasks();
      loadStatus();
      showNotification('Đã thêm task vào hàng đợi', 'success');
    } catch (error) {
      showNotification('Lỗi khi thêm vào hàng đợi: ' + getErrorMessage(error), 'error');
    }
  };

  const removeFromQueue = async (taskId) => {
    try {
      await axios.post(`/api/queue/remove/${taskId}`);
      loadTasks();
      loadStatus();
      showNotification('Đã xóa task khỏi hàng đợi', 'success');
    } catch (error) {
      showNotification('Lỗi khi xóa khỏi hàng đợi: ' + getErrorMessage(error), 'error');
    }
  };

  const uploadImage = async (file) => {
    const formData = new FormData();
    formData.append('image', file);

    setUploadStatus('Đang upload...');
    try {
      const response = await axios.post('/api/upload-image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setUploadedImagePath(response.data.image_path);
      setUploadStatus('Upload thành công!');
      showNotification('Upload ảnh thành công!', 'success');
      return response.data.image_path;
    } catch (error) {
      setUploadStatus('Upload thất bại');
      showNotification('Lỗi upload ảnh: ' + getErrorMessage(error), 'error');
      return null;
    }
  };

  const handleImageSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedImage(file);
      uploadImage(file);
      // Reset input để cho phép chọn lại cùng một file
      event.target.value = '';
    }
  };

  // Character analysis function
  const analyzeCharacter = async () => {
    if (!uploadedImagePath) {
      showNotification('Vui lòng upload ảnh trước khi phân tích nhân vật', 'warning');
      return;
    }

    setAnalyzingCharacter(true);
    try {
      const response = await axios.post('/api/analyze-character', {
        image_path: uploadedImagePath
      });

      if (response.data.success) {
        setCharacterAnalysis(response.data.analysis);
        showNotification('Phân tích nhân vật thành công!', 'success');
      } else {
        showNotification('Lỗi khi phân tích nhân vật: ' + response.data.error, 'error');
      }
    } catch (error) {
      showNotification('Lỗi khi phân tích nhân vật: ' + getErrorMessage(error), 'error');
    } finally {
      setAnalyzingCharacter(false);
    }
  };

  const deleteTask = async (taskId) => {
    try {
      await axios.delete(`/api/tasks/${taskId}`);
      loadTasks();
      showNotification('Xóa task thành công!', 'success');
    } catch (error) {
      showNotification('Lỗi khi xóa task: ' + getErrorMessage(error), 'error');
    }
  };

  const viewTaskDetails = (task) => {
    setSelectedTask(task);
    setActiveTab('details');
  };

  const addPrompt = () => {
    setPrompts([...prompts, '']);
  };

  const removePrompt = (index) => {
    if (prompts.length > 1) {
      setPrompts(prompts.filter((_, i) => i !== index));
    }
  };

  const updatePrompt = (index, value) => {
    const newPrompts = [...prompts];
    newPrompts[index] = value;
    setPrompts(newPrompts);
  };

  const splitPrompts = async () => {
    if (!bulkText.trim()) {
      showNotification('Vui lòng nhập text để phân tách', 'warning');
      return;
    }

    setProcessingPrompts(true);
    try {
      const response = await axios.post('/api/split-prompts', {
        text: bulkText,
        use_ai: useAI
      });

      if (response.data.success) {
        setPrompts(response.data.prompts);
        setBulkText('');
        showNotification(
          `Đã phân tách thành công ${response.data.count} prompt! ${response.data.analysis}`, 
          'success'
        );
      }
    } catch (error) {
      showNotification('Lỗi khi phân tách prompt: ' + getErrorMessage(error), 'error');
    } finally {
      setProcessingPrompts(false);
    }
  };

  const clearPrompts = () => {
    setPrompts(['']);
    setBulkText('');
    showNotification('Đã xóa tất cả prompt!', 'success');
  };

  const downloadAllImages = (taskId) => {
    // Tạo link tải xuống và click
    const link = document.createElement('a');
    link.href = `/api/download-all-images/${taskId}`;
    link.download = `task_${taskId}_images.zip`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showNotification('Đang tải xuống tất cả ảnh...', 'success');
  };

  const downloadSingleImage = (filename) => {
    // Tạo link tải xuống và click
    const link = document.createElement('a');
    link.href = `/api/download-image/${filename}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showNotification(`Đang tải xuống ${filename}...`, 'success');
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle className="status-icon completed" />;
      case 'processing': return <RefreshCw className="status-icon processing" />;
      case 'failed': return <XCircle className="status-icon failed" />;
      case 'partial': return <AlertCircle className="status-icon partial" />;
      case 'queued': return <Clock className="status-icon queued" />;
      default: return <Clock className="status-icon pending" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'completed': return 'Hoàn thành';
      case 'processing': return 'Đang xử lý';
      case 'failed': return 'Thất bại';
      case 'partial': return 'Một phần';
      case 'pending': return 'Chờ xử lý';
      case 'queued': return 'Trong hàng đợi';
      default: return status;
    }
  };

  const formatDateTime = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleString('vi-VN');
  };

  return (
    <div className="app">
      {/* Notification System */}
      {notification && (
        <div className={`notification notification-${notification.type}`}>
          <div className="notification-content">
            <span className="notification-message">{notification.message}</span>
            <button 
              className="notification-close"
              onClick={() => setNotification(null)}
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="header">
        <div className="header-content">
          <h1>Gemini AI</h1>
          <div className="status-indicator">
            <span className="status-dot"></span>
            <span>Tất cả API keys: {apiKeys.length} | Tasks: {tasks.length}</span>
          </div>
        </div>
      </header>

      <div className="main-container">
        {/* Sidebar */}
        <aside className="sidebar">
          <nav className="nav-menu">
            <button 
              className={`nav-item ${activeTab === 'home' ? 'active' : ''}`}
              onClick={() => setActiveTab('home')}
            >
              <Home size={20} />
              <span>Tạo ảnh</span>
            </button>
            <button 
              className={`nav-item ${activeTab === 'tasks' ? 'active' : ''}`}
              onClick={() => setActiveTab('tasks')}
            >
              <Settings size={20} />
              <span>Lịch sử</span>
            </button>
            <button 
              className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
              onClick={() => setActiveTab('settings')}
            >
              <Settings size={20} />
              <span>Cài đặt</span>
            </button>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="main-content">
          {/* Home Tab - Create Images */}
          {activeTab === 'home' && (
            <div className="tab-content">
              <div className="tab-header">
                <h2>Tạo ảnh với Gemini AI</h2>
                <p>Tạo ảnh từ văn bản với nhiều API keys</p>
              </div>

              <div className="create-section">
                {/* System Status */}
                <div className="status-card">
                  <h3>Trạng thái hệ thống</h3>
                  <div className="status-grid">
                    <div className="status-item">
                      <span className="label">API Keys:</span>
                      <span className="value">{status.total_api_keys || apiKeys.length}</span>
                    </div>
                    <div className="status-item">
                      <span className="label">Khả dụng:</span>
                      <span className="value">{status.available_keys || 0}</span>
                    </div>
                    <div className="status-item">
                      <span className="label">Bị lỗi:</span>
                      <span className="value">{status.failed_keys || 0}</span>
                    </div>
                  </div>
                  
                  {/* Queue Status */}
                  <div className="queue-status">
                    <h4>📋 Hàng đợi:</h4>
                    <div className="queue-grid">
                      <div className="queue-item">
                        <span className="label">Đang chờ:</span>
                        <span className="value pending">{status.pending_tasks || 0}</span>
                      </div>
                      <div className="queue-item">
                        <span className="label">Trong hàng đợi:</span>
                        <span className="value queued">{status.queued_tasks || 0}</span>
                      </div>
                      <div className="queue-item">
                        <span className="label">Đang xử lý:</span>
                        <span className="value processing">{status.processing_tasks || 0}</span>
                      </div>
                      <div className="queue-item">
                        <span className="label">Hoàn thành:</span>
                        <span className="value completed">{status.completed_tasks || 0}</span>
                      </div>
                    </div>
                    {status.queue && status.queue.is_processing && (
                      <div className="active-queue">
                        <span className="processing-indicator">🔄 Đang xử lý task...</span>
                      </div>
                    )}
                  </div>
                  
                  {/* Free Tier Info */}
                  <div className="free-tier-info">
                    <h4>📋 Thông tin Model:</h4>
                    <div className="tier-details">
                      <div className="tier-item">
                        <span className="model">✅ Model: gemini-2.0-flash-preview-image-generation</span>
                      </div>
                      <div className="tier-item">
                        <span className="label">Trạng thái:</span>
                        <span className="value success">✅ Hoạt động với cấu hình đúng</span>
                      </div>
                      <div className="tier-item">
                        <span className="label">Khả năng:</span>
                        <span className="value success">✅ Image Generation (TEXT + IMAGE input)</span>
                      </div>
                      <div className="tier-item">
                        <span className="label">Tính năng:</span>
                        <span className="value">Image-to-Image, Text-to-Image, Prompt Splitting</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Upload Image Section */}
                <div className="upload-section">
                  <h3>Upload ảnh nhân vật (tùy chọn)</h3>
                  <div className="upload-area">
                    <input
                      type="file"
                      id="image-upload"
                      accept="image/*"
                      onChange={handleImageSelect}
                      style={{ display: 'none' }}
                    />
                    <label htmlFor="image-upload" className="upload-button">
                      <Upload size={24} />
                      <span>{selectedImage ? 'Thay đổi ảnh' : 'Chọn ảnh'}</span>
                    </label>
                    
                    {selectedImage && (
                      <div className="image-preview">
                        <img 
                          src={URL.createObjectURL(selectedImage)} 
                          alt="Preview" 
                          className="preview-img"
                        />
                        <div className="image-info">
                          <span className="file-name">{selectedImage.name}</span>
                          <span className={`upload-status ${uploadStatus.includes('thành công') ? 'success' : uploadStatus.includes('thất bại') ? 'error' : ''}`}>
                            {uploadStatus || 'Đã chọn'}
                          </span>
                        </div>
                        <button 
                          onClick={() => {
                            setSelectedImage(null);
                            setUploadedImagePath(null);
                            setUploadStatus('');
                            setCharacterSync(false);
                            setCharacterAnalysis('');
                          }}
                          className="remove-image-btn"
                          title="Xóa ảnh"
                        >
                          <X size={16} />
                        </button>
                      </div>
                    )}

                    {/* Character Sync Section */}
                    {selectedImage && (
                      <div className="character-sync-section">
                        <h4>🎭 Đồng bộ hóa nhân vật</h4>
                        <div className="sync-controls">
                          <div className="sync-checkbox">
                            <input
                              type="checkbox"
                              id="character-sync"
                              checked={characterSync}
                              onChange={(e) => setCharacterSync(e.target.checked)}
                            />
                            <label htmlFor="character-sync">
                              Bật đồng bộ hóa nhân vật
                            </label>
                          </div>
                          
                          {characterSync && (
                            <div className="analyze-section">
                              <button
                                onClick={analyzeCharacter}
                                disabled={analyzingCharacter}
                                className="analyze-btn"
                              >
                                {analyzingCharacter ? (
                                  <>
                                    <RefreshCw size={16} className="spinning" />
                                    Đang phân tích...
                                  </>
                                ) : (
                                  <>
                                    <Image size={16} />
                                    Phân tích nhân vật
                                  </>
                                )}
                              </button>
                              
                              {characterAnalysis && (
                                <div className="character-analysis">
                                  <h5>📝 Phân tích nhân vật:</h5>
                                  <div className="analysis-content">
                                    {characterAnalysis}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Prompt Processing Section */}
                <div className="prompt-processing-section">
                  <h3>Phân tách prompt từ text</h3>
                  <p className="section-description">
                    Nhập một đoạn text chứa nhiều yêu cầu tạo ảnh, AI sẽ tự động phân tách thành các prompt riêng biệt
                  </p>
                  
                  <div className="input-group">
                    <label>Text chứa các prompt:</label>
                    <textarea
                      value={bulkText}
                      onChange={(e) => setBulkText(e.target.value)}
                      placeholder="Ví dụ:
1. Một ngôi nhà nhỏ màu xanh trên đồi cỏ
2. Con mèo trắng đang ngủ trên ghế sofa
3. Bình hoa hồng đỏ đặt trên bàn gỗ
4. Cảnh hoàng hôn trên biển với thuyền buồm"
                      className="text-input bulk-text-input"
                      rows={6}
                    />
                  </div>

                  <div className="processing-options">
                    <div className="checkbox-group">
                      <input
                        type="checkbox"
                        id="use-ai"
                        checked={useAI}
                        onChange={(e) => setUseAI(e.target.checked)}
                      />
                      <label htmlFor="use-ai">Sử dụng AI để phân tích (chính xác hơn)</label>
                    </div>
                  </div>

                  <div className="processing-actions">
                    <button
                      onClick={splitPrompts}
                      disabled={processingPrompts || !bulkText.trim()}
                      className="process-button"
                    >
                      {processingPrompts ? (
                        <>
                          <RefreshCw size={20} className="spinning" />
                          Đang phân tích...
                        </>
                      ) : (
                        <>
                          <RefreshCw size={20} />
                          Phân tách prompt
                        </>
                      )}
                    </button>
                    
                    <button
                      onClick={clearPrompts}
                      disabled={processingPrompts}
                      className="clear-button"
                    >
                      <Trash2 size={20} />
                      Xóa tất cả
                    </button>
                  </div>
                </div>

                {/* Create Batch Section */}
                <div className="batch-section">
                  <h3>Tạo batch</h3>
                  
                  <div className="input-group">
                    <label>Tên batch:</label>
                    <input
                      type="text"
                      value={batchName}
                      onChange={(e) => setBatchName(e.target.value)}
                      placeholder="Nhập tên batch"
                      className="text-input"
                    />
                  </div>

                  <div className="prompts-section">
                    <div className="prompts-header">
                      <label>Danh sách prompts:</label>
                      <button 
                        type="button" 
                        onClick={addPrompt}
                        className="add-button"
                      >
                        <Plus size={16} />
                        Thêm prompt
                      </button>
                    </div>
                    
                    {prompts.map((prompt, index) => (
                      <div key={index} className="prompt-item">
                        <input
                          type="text"
                          value={prompt}
                          onChange={(e) => updatePrompt(index, e.target.value)}
                          placeholder={`Prompt ${index + 1}`}
                          className="text-input prompt-input"
                        />
                        {prompts.length > 1 && (
                          <button
                            type="button"
                            onClick={() => removePrompt(index)}
                            className="remove-button"
                          >
                            <Trash2 size={16} />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>

                  <button
                    onClick={createBatchTask}
                    disabled={loading || apiKeys.length === 0}
                    className="create-button"
                  >
                    {loading ? (
                      <>
                        <RefreshCw size={20} className="spinning" />
                        Đang tạo...
                      </>
                    ) : (
                      <>
                        <Plus size={20} />
                        Tạo batch
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Tasks Tab - History */}
          {activeTab === 'tasks' && (
            <div className="tab-content">
              <div className="tab-header">
                <h2>Lịch sử tasks</h2>
                <button onClick={loadTasks} className="refresh-button">
                  <RefreshCw size={16} />
                  Làm mới
                </button>
              </div>

              <div className="tasks-grid">
                {Object.values(tasks).length === 0 ? (
                  <div className="empty-state">
                    <Image size={48} />
                    <p>Chưa có task nào</p>
                  </div>
                ) : (
                  Object.values(tasks)
                    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at)) // Sắp xếp mới nhất lên đầu
                    .map((task) => (
                      <div key={task.id} className="task-card">
                        <div className="task-header">
                          <h3>{task.name}</h3>
                          <div className="task-status">
                            {getStatusIcon(task.status)}
                            <span>{getStatusText(task.status)}</span>
                          </div>
                        </div>
                        
                        {/* Thanh tiến trình */}
                        <div className="progress-section">
                          <div className="progress-bar">
                            <div 
                              className="progress-fill"
                              style={{ 
                                width: `${task.total_count > 0 ? (task.completed_count / task.total_count) * 100 : 0}%`,
                                backgroundColor: task.status === 'completed' ? '#10b981' : 
                                               task.status === 'failed' ? '#ef4444' : '#3b82f6'
                              }}
                            ></div>
                          </div>
                          <div className="progress-info">
                            <span>{task.completed_count}/{task.total_count}</span>
                            {task.failed_count > 0 && (
                              <span className="failed-count">Thất bại: {task.failed_count}</span>
                            )}
                          </div>
                        </div>
                        
                        <div className="task-info">
                          <div className="task-meta">
                            <span>Tạo: {formatDateTime(task.created_at)}</span>
                            {task.updated_at !== task.created_at && (
                              <span>Cập nhật: {formatDateTime(task.updated_at)}</span>
                            )}
                          </div>
                        </div>

                        <div className="task-actions">
                          {/* Nút quản lý hàng đợi */}
                          {task.status === 'pending' && (
                            <button
                              onClick={() => startTaskManual(task.id)}
                              className="action-button start"
                              title="Chạy task thủ công"
                            >
                              <Play size={16} />
                              Chạy
                            </button>
                          )}
                          
                          {task.status === 'queued' && (
                            <button
                              onClick={() => removeFromQueue(task.id)}
                              className="action-button remove-queue"
                              title="Xóa khỏi hàng đợi"
                            >
                              <XCircle size={16} />
                              Bỏ hàng đợi
                            </button>
                          )}
                          
                          {(task.status === 'pending' || task.status === 'failed') && (
                            <button
                              onClick={() => addToQueue(task.id)}
                              className="action-button add-queue"
                              title="Thêm vào hàng đợi"
                            >
                              <Clock size={16} />
                              Thêm hàng đợi
                            </button>
                          )}
                          
                          <button
                            onClick={() => viewTaskDetails(task)}
                            className="action-button view"
                          >
                            <Eye size={16} />
                            Chi tiết
                          </button>
                          <button
                            onClick={() => deleteTask(task.id)}
                            className="action-button delete"
                          >
                            <Trash2 size={16} />
                            Xóa
                          </button>
                        </div>
                      </div>
                    ))
                )}
              </div>
            </div>
          )}

          {/* Settings Tab */}
          {activeTab === 'settings' && (
            <div className="tab-content">
              <div className="tab-header">
                <h2>Quản lý API Keys</h2>
              </div>

              <div className="settings-section">
                <div className="input-group">
                  <label>Thêm API key mới:</label>
                  <div className="input-with-button">
                    <input
                      type="password"
                      value={newApiKey}
                      onChange={(e) => setNewApiKey(e.target.value)}
                      placeholder="Nhập API key của Gemini"
                      className="text-input"
                    />
                    <button
                      onClick={addApiKey}
                      disabled={loading || !newApiKey.trim()}
                      className="add-key-button"
                    >
                      {loading ? 'Đang thêm...' : 'Thêm'}
                    </button>
                  </div>
                </div>

                <div className="api-keys-list">
                  <h3>API Keys hiện tại ({apiKeys.length})</h3>
                  {apiKeys.length === 0 ? (
                    <div className="empty-state">
                      <AlertCircle size={32} />
                      <p>Chưa có API key nào</p>
                    </div>
                  ) : (
                    <div className="keys-grid">
                      {apiKeys.map((key, index) => (
                        <div key={index} className="key-item">
                          <div className="key-display">
                            <span className="key-prefix">••••••••</span>
                            <span className="key-suffix">{key.slice(-8)}</span>
                          </div>
                          <button
                            onClick={() => removeApiKey(key.slice(-8))}
                            className="remove-key-button"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Task Details Modal */}
          {activeTab === 'details' && selectedTask && (
            <div className="tab-content">
              <div className="tab-header">
                <button 
                  onClick={() => setActiveTab('tasks')}
                  className="back-button"
                >
                  ← Quay lại
                </button>
                <h2>Chi tiết task: {selectedTask.name}</h2>
              </div>

              <div className="task-details">
                <div className="detail-section">
                  <h3>Thông tin chung</h3>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <span className="label">Trạng thái:</span>
                      <span className={`value status-${selectedTask.status}`}>
                        {getStatusIcon(selectedTask.status)}
                        {getStatusText(selectedTask.status)}
                      </span>
                    </div>
                    <div className="detail-item">
                      <span className="label">Tiến độ:</span>
                      <span className="value">{selectedTask.completed_count}/{selectedTask.total_count}</span>
                    </div>
                    <div className="detail-item">
                      <span className="label">Thất bại:</span>
                      <span className="value failed">{selectedTask.failed_count}</span>
                    </div>
                    <div className="detail-item">
                      <span className="label">Tạo lúc:</span>
                      <span className="value">{formatDateTime(selectedTask.created_at)}</span>
                    </div>
                    <div className="detail-item">
                      <span className="label">Cập nhật:</span>
                      <span className="value">{formatDateTime(selectedTask.updated_at)}</span>
                    </div>
                  </div>
                </div>

                <div className="detail-section">
                  <div className="section-header">
                    <h3>Kết quả ({selectedTask.results.length})</h3>
                    {selectedTask.results.length > 0 && (
                      <button 
                        className="download-all-button"
                        onClick={() => downloadAllImages(selectedTask.id)}
                      >
                        <Download size={16} />
                        Tải tất cả ảnh
                      </button>
                    )}
                  </div>
                  <div className="results-list">
                    {selectedTask.results.map((result, index) => (
                      <div key={index} className={`result-item ${result.status}`}>
                        <div className="result-header">
                          <span className="result-number">#{index + 1}</span>
                          <span className={`result-status ${result.status}`}>
                            {result.status === 'success' ? <CheckCircle size={16} /> : <XCircle size={16} />}
                            {result.status === 'success' ? 'Thành công' : 'Thất bại'}
                          </span>
                        </div>
                        
                        <div className="result-content">
                          <div className="result-prompt">
                            <strong>Prompt:</strong> {result.prompt}
                          </div>
                          
                          {result.status === 'success' ? (
                            <div className="result-success">
                              <div className="image-result">
                                <img src={`/api/images/${result.filename}`} alt="Generated" />
                                <div className="image-actions">
                                  <button 
                                    className="download-button"
                                    onClick={() => downloadSingleImage(result.filename)}
                                  >
                                    <Download size={16} />
                                    Tải xuống
                                  </button>
                                  <button 
                                    className="view-button"
                                    onClick={() => window.open(`/api/images/${result.filename}`, '_blank')}
                                  >
                                    <Eye size={16} />
                                    Xem ảnh
                                  </button>
                                </div>
                              </div>
                              {result.api_key_used && (
                                <div className="api-info">
                                  <span>API Key: {result.api_key_used}</span>
                                </div>
                              )}
                            </div>
                          ) : (
                            <div className="result-error">
                              <strong>Lỗi:</strong> {result.error}
                            </div>
                          )}
                          
                          <div className="result-time">
                            {formatDateTime(result.timestamp)}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
