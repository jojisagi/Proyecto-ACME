import React from 'react';
import './OrderList.css';

function OrderList({ orders, onViewOrder }) {
  const getStatusBadge = (status) => {
    const statusMap = {
      'PENDING': { label: 'Pendiente', color: '#ffa500' },
      'PAYMENT_PROCESSED': { label: 'Pago Procesado', color: '#4169e1' },
      'SHIPPED': { label: 'Enviado', color: '#9370db' },
      'DELIVERED': { label: 'Entregado', color: '#32cd32' },
      'PAYMENT_FAILED': { label: 'Pago Fallido', color: '#dc143c' }
    };
    
    const statusInfo = statusMap[status] || { label: status, color: '#808080' };
    
    return (
      <span 
        className="status-badge" 
        style={{ backgroundColor: statusInfo.color }}
      >
        {statusInfo.label}
      </span>
    );
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (orders.length === 0) {
    return (
      <div className="empty-state">
        <h2>📦 No hay órdenes</h2>
        <p>Crea tu primera orden para comenzar</p>
      </div>
    );
  }

  return (
    <div className="order-list">
      <h2>📋 Lista de Órdenes ({orders.length})</h2>
      
      <div className="orders-grid">
        {orders.map((order) => (
          <div key={order.orderId} className="order-card">
            <div className="order-header">
              <h3>#{order.orderId.substring(0, 8)}</h3>
              {getStatusBadge(order.status)}
            </div>
            
            <div className="order-body">
              <p className="customer-name">
                <strong>👤 {order.customerName}</strong>
              </p>
              <p className="order-date">
                📅 {formatDate(order.orderDate)}
              </p>
              <p className="order-items">
                📦 {order.items?.length || 0} item(s)
              </p>
              <p className="order-total">
                <strong>💰 ${order.totalAmount}</strong>
              </p>
            </div>
            
            <div className="order-footer">
              <button 
                onClick={() => onViewOrder(order.orderId)}
                className="view-button"
              >
                Ver Detalles →
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default OrderList;
