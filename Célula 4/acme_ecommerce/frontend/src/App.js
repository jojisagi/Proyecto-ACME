import React, { useState, useEffect } from 'react';
import './App.css';
import OrderList from './components/OrderList';
import OrderForm from './components/OrderForm';
import OrderDetail from './components/OrderDetail';
import { getOrders, createOrder, getOrder } from './services/api';

function App() {
  const [orders, setOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [view, setView] = useState('list'); // 'list', 'create', 'detail'

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getOrders();
      setOrders(data);
    } catch (err) {
      setError('Error cargando órdenes: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOrder = async (orderData) => {
    setLoading(true);
    setError(null);
    try {
      const newOrder = await createOrder(orderData);
      setOrders([newOrder, ...orders]);
      setView('list');
      alert('¡Orden creada exitosamente!');
    } catch (err) {
      setError('Error creando orden: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleViewOrder = async (orderId) => {
    setLoading(true);
    setError(null);
    try {
      const order = await getOrder(orderId);
      setSelectedOrder(order);
      setView('detail');
    } catch (err) {
      setError('Error cargando orden: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🛒 E-commerce AWS Serverless</h1>
        <p>Arquitectura con Lambda, Step Functions y DynamoDB</p>
      </header>

      <nav className="App-nav">
        <button 
          onClick={() => setView('list')}
          className={view === 'list' ? 'active' : ''}
        >
          📋 Órdenes
        </button>
        <button 
          onClick={() => setView('create')}
          className={view === 'create' ? 'active' : ''}
        >
          ➕ Nueva Orden
        </button>
        <button onClick={loadOrders}>
          🔄 Recargar
        </button>
      </nav>

      <main className="App-main">
        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        {loading && (
          <div className="loading">
            Cargando...
          </div>
        )}

        {!loading && view === 'list' && (
          <OrderList 
            orders={orders} 
            onViewOrder={handleViewOrder}
          />
        )}

        {!loading && view === 'create' && (
          <OrderForm 
            onSubmit={handleCreateOrder}
            onCancel={() => setView('list')}
          />
        )}

        {!loading && view === 'detail' && selectedOrder && (
          <OrderDetail 
            order={selectedOrder}
            onBack={() => setView('list')}
          />
        )}
      </main>

      <footer className="App-footer">
        <p>AWS Serverless Architecture Demo</p>
      </footer>
    </div>
  );
}

export default App;
