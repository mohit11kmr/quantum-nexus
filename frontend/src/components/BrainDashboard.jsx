import React, { useCallback, useEffect, useRef, useState } from 'react';
import { fetchBrainStatus, fetchBrainScenarios, optimizeBrain, fetchBrainTask } from '../services/api';

const POLL_INTERVAL_MS = 2000;

export default function BrainDashboard() {
  const [status, setStatus] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [task, setTask] = useState(null);
  const [training, setTraining] = useState(false);
  const pollRef = useRef(null);

  const refreshStatus = useCallback(() => {
    fetchBrainStatus().then(setStatus).catch(() => {});
  }, []);

  useEffect(() => {
    refreshStatus();
    fetchBrainScenarios().then(res => {
      const list = Array.isArray(res) ? res : (res?.scenarios || []);
      setScenarios(list);
    });
  }, [refreshStatus]);

  useEffect(() => () => {
    if (pollRef.current) clearInterval(pollRef.current);
  }, []);

  const pollTask = useCallback(async (taskId) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      const t = await fetchBrainTask(taskId);
      if (!t || t.status === 'FAILED' || t.status === 'SUCCEEDED') {
        clearInterval(pollRef.current);
        pollRef.current = null;
        setTask(t || null);
        setTraining(false);
        refreshStatus();
      } else {
        setTask(t);
      }
    }, POLL_INTERVAL_MS);
  }, [refreshStatus]);

  const handleRetrain = async () => {
    setTraining(true);
    setTask({ status: 'QUEUED', progress: 0, note: 'Submitting training job…' });
    const res = await optimizeBrain({ light: true, symbols: 8, epochs: 12 });
    if (res?.task_id) {
      setTask(res);
      pollTask(res.task_id);
    } else {
      setTask({ status: 'FAILED', error: res?.error || 'Could not start training' });
      setTraining(false);
    }
  };

  const scenarioList = Array.isArray(scenarios) ? scenarios : [];

  const taskStatusLabel = task?.status || 'IDLE';
  const taskProgress = task?.progress || 0;
  const taskResult = task?.result;

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">AI Brain & Zero-Loss Optimizer</div>
        <button className="btn btn-primary" onClick={handleRetrain} disabled={training}>
          {training ? 'Training…' : 'Force Retrain'}
        </button>
      </div>

      {status && (
        <div className="metrics-row" style={{ marginBottom: '1.5rem' }}>
          <div className="metric-card">
            <div className="metric-title">Architecture</div>
            <div className="metric-value" style={{ fontSize: '0.95rem' }}>{status.model_architecture || 'Multi-Model Ensemble'}</div>
          </div>
          <div className="metric-card">
            <div className="metric-title">Memory Samples</div>
            <div className="metric-value">{status.memory_samples_count ?? 0}</div>
          </div>
          <div className="metric-card">
            <div className="metric-title">Status</div>
            <div className="metric-value" style={{ color: status.is_trained ? 'var(--accent-green)' : 'var(--accent-gold)' }}>
              {status.is_trained ? 'TRAINED' : 'COLD START'}
            </div>
          </div>
        </div>
      )}

      <div style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '0.75rem' }}>Background Training Task</h3>
        <div className="card" style={{ padding: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span className={`badge ${taskStatusLabel === 'SUCCEEDED' ? 'badge-success' : taskStatusLabel === 'FAILED' ? 'badge-danger' : taskStatusLabel === 'IDLE' ? 'badge-warning' : 'badge-warning'}`}>
                {taskStatusLabel}
              </span>
              <span className="text-secondary" style={{ fontSize: '0.85rem' }}>
                {task?.error || task?.note || (taskStatusLabel === 'IDLE' ? 'No training job running — click Force Retrain.' : `Light mode · ${task?.symbols || 8} symbols · ${task?.epochs || 12} epochs`)}
              </span>
            </div>
          </div>
          {(taskStatusLabel === 'QUEUED' || taskStatusLabel === 'RUNNING') && (
            <div style={{ marginTop: '0.75rem', background: 'rgba(255,255,255,0.08)', height: '8px', borderRadius: '4px' }}>
              <div style={{ width: `${Math.max(5, taskProgress)}%`, height: '100%', background: 'var(--accent-blue)', borderRadius: '4px', transition: 'width 0.5s ease' }} />
            </div>
          )}
          {taskResult && (
            <div style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              <div>RandomForest: <b>{taskResult.randomForest?.accuracyPct}%</b> accuracy · {taskResult.randomForest?.patternsLearned} patterns</div>
              <div>LSTM: <b>{taskResult.lstm?.trainAccuracyPct}%</b> train / <b>{taskResult.lstm?.validationAccuracyPct}%</b> val accuracy · {taskResult.lstm?.epochsTrained} epochs</div>
            </div>
          )}
        </div>
      </div>

      <div>
        <h3 style={{ marginBottom: '1rem' }}>Zero-Loss Scenario Ranker</h3>
        <table className="data-table">
          <thead>
            <tr><th>Scenario Name</th><th>Probability</th><th>AI Recommended Action</th></tr>
          </thead>
          <tbody>
            {scenarioList.map((s, i) => {
              const prob = typeof s.probability === 'number' ? s.probability : (s.prob || 0.5);
              return (
                <tr key={i}>
                  <td>{s.name || `Scenario #${i + 1}`}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      <div style={{ flex: 1, background: 'rgba(255,255,255,0.1)', height: '8px', borderRadius: '4px' }}>
                        <div style={{ width: `${(prob <= 1 ? prob * 100 : prob).toFixed(0)}%`, height: '100%', background: 'var(--accent-blue)', borderRadius: '4px' }} />
                      </div>
                      <span>{(prob <= 1 ? prob * 100 : prob).toFixed(0)}%</span>
                    </div>
                  </td>
                  <td><span className="badge badge-warning">HEDGE</span></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
