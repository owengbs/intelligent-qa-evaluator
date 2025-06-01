import React from 'react';
import { Provider } from 'react-redux';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { store } from './store/store';
import EvaluationForm from './components/EvaluationForm';
import './App.css';

function App() {
  return (
    <Provider store={store}>
      <ConfigProvider locale={zhCN}>
        <div className="App">
          <header className="App-header">
            <h1>智能问答助手自动评估系统</h1>
            <p>基于大模型的问答质量评估平台</p>
          </header>
          <main className="App-main">
            <EvaluationForm />
          </main>
        </div>
      </ConfigProvider>
    </Provider>
  );
}

export default App; 