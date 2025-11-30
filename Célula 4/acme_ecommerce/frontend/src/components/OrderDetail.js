import React from 'react';
import './OrderDetail.css';

function OrderDetail({ order, onBack }) {
  const getStatusBadge = (status) => {
    const statusMap = {
      'PENDING': { label: 'Pendiente', color: '#ffa500', icon: '⏳' },
      'PAYMENT_PROCESSED': { label: 'Pago Procesado', color: '#4169e1', icon: '💳' },
      'SHIPPED': { label: 'Enviado', color: '#9370db', icon: '🚚' },
      'DELIVERED': { label: 'Entregado', color: '#32cd32', icon: '✅' },
      'PAYMENT_FAILED': { label: 'Pago Fallido', color: '#dc143c', icon: '❌' }
    };
    
    const statusInfo = statusMap[status] || { label: status, color: '#808080', icon: '❓' };
    
    return (
      <div className="status-badge-large" style={{ backgroundColor: statusInfo.color }}>
        <span className="status-icon">{statusInfo.icon}</span>
        <span>{statusInfo.label}</span>
      </div>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="order-detail-container">
      <button onClick={onBack} className="back-button">
        ← Volver a la lista
      </button>

      <div className="order-detail">
        <div className="detail-header">
          <div>
            <h2>Orden #{order.orderId}</h2>
            <p className="order-date">Creada: {formatDate(order.orderDate)}</p>
          </div>
          {getStatusBadge(order.status)}
        </div>

        <div className="detail-grid">
          {/* Información del Cliente */}
          <section className="detail-section">
            <h3>👤 Cliente</h3>
            <div className="detail-content">
              <p><strong>ID:</strong> {order.customerId}</p>
              <p><strong>Nombre:</strong> {order.customerName}</p>
              <p><strong>Email:</strong> {order.customerEmail}</p>
              <p><strong>Método de Pago:</strong> {order.paymentMethod}</p>
            </div>
          </section>

          {/* Dirección de Envío */}
          <section className="detail-section">
            <h3>📍 Dirección de Envío</h3>
            <div className="detail-content">
              <p>{order.shippingAddress?.street}</p>
              <p>{order.shippingAddress?.city}, {order.shippingAddress?.state}</p>
              <p>{order.shippingAddress?.zipCode}</p>
              <p>{order.shippingAddress?.country}</p>
            </div>
          </section>

          {/* Información de Pago */}
          {order.paymentDate && (
            <section className="detail-section">
              <h3>💳 Pago</h3>
              <div className="detail-content">
                <p><strong>Fecha:</strong> {formatDate(order.paymentDate)}</p>
                {order.transactionId && (
                  <p><strong>ID Transacción:</strong> {order.transactionId}</p>
                )}
              </div>
            </section>
          )}

          {/* Información de Envío */}
          {order.shipmentDate && (
            <section className="detail-section">
              <h3>🚚 Envío</h3>
              <div className="detail-content">
                <p><strong>Fecha de Envío:</strong> {formatDate(order.shipmentDate)}</p>
                {order.trackingNumber && (
                  <p><strong>Tracking:</strong> {order.trackingNumber}</p>
                )}
                {order.estimatedDeliveryDays && (
                  <p><strong>Entrega Estimada:</strong> {order.estimatedDeliveryDays} días</p>
                )}
                {order.deliveryDate && (
                  <p><strong>Fecha de Entrega:</strong> {formatDate(order.deliveryDate)}</p>
                )}
              </div>
            </section>
          )}
        </div>

        {/* Productos */}
        <section className="detail-section full-width">
          <h3>📦 Productos</h3>
          <div className="items-table">
            <table>
              <thead>
                <tr>
                  <th>ID Producto</th>
                  <th>Nombre</th>
                  <th>Cantidad</th>
                  <th>Precio Unit.</th>
                  <th>Subtotal</th>
                </tr>
              </thead>
              <tbody>
                {order.items?.map((item, index) => (
                  <tr key={index}>
                    <td>{item.productId}</td>
                    <td>{item.name}</td>
                    <td>{item.quantity}</td>
                    <td>${item.price}</td>
                    <td>${(item.quantity * item.price).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Total */}
        <div className="order-total-detail">
          <h3>Total: ${order.totalAmount}</h3>
        </div>
      </div>
    </div>
  );
}

export default OrderDetail;
