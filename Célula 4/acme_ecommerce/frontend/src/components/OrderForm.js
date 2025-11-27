import React, { useState } from 'react';
import './OrderForm.css';

function OrderForm({ onSubmit, onCancel }) {
  const [formData, setFormData] = useState({
    customerId: '',
    customerName: '',
    customerEmail: '',
    paymentMethod: 'credit_card',
    shippingAddress: {
      street: '',
      city: '',
      state: '',
      zipCode: '',
      country: 'España'
    },
    items: [
      { productId: '', name: '', quantity: 1, price: 0 }
    ]
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleAddressChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      shippingAddress: {
        ...prev.shippingAddress,
        [name]: value
      }
    }));
  };

  const handleItemChange = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index][field] = field === 'quantity' || field === 'price' 
      ? parseFloat(value) || 0 
      : value;
    setFormData(prev => ({
      ...prev,
      items: newItems
    }));
  };

  const addItem = () => {
    setFormData(prev => ({
      ...prev,
      items: [...prev.items, { productId: '', name: '', quantity: 1, price: 0 }]
    }));
  };

  const removeItem = (index) => {
    if (formData.items.length > 1) {
      setFormData(prev => ({
        ...prev,
        items: prev.items.filter((_, i) => i !== index)
      }));
    }
  };

  const calculateTotal = () => {
    return formData.items.reduce((sum, item) => {
      return sum + (item.quantity * item.price);
    }, 0).toFixed(2);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    const orderData = {
      ...formData,
      totalAmount: parseFloat(calculateTotal())
    };
    
    onSubmit(orderData);
  };

  return (
    <div className="order-form-container">
      <h2>➕ Nueva Orden</h2>
      
      <form onSubmit={handleSubmit} className="order-form">
        {/* Información del Cliente */}
        <section className="form-section">
          <h3>👤 Información del Cliente</h3>
          
          <div className="form-group">
            <label>ID Cliente *</label>
            <input
              type="text"
              name="customerId"
              value={formData.customerId}
              onChange={handleChange}
              required
              placeholder="cust-001"
            />
          </div>

          <div className="form-group">
            <label>Nombre *</label>
            <input
              type="text"
              name="customerName"
              value={formData.customerName}
              onChange={handleChange}
              required
              placeholder="Juan Pérez"
            />
          </div>

          <div className="form-group">
            <label>Email *</label>
            <input
              type="email"
              name="customerEmail"
              value={formData.customerEmail}
              onChange={handleChange}
              required
              placeholder="juan@email.com"
            />
          </div>

          <div className="form-group">
            <label>Método de Pago *</label>
            <select
              name="paymentMethod"
              value={formData.paymentMethod}
              onChange={handleChange}
              required
            >
              <option value="credit_card">Tarjeta de Crédito</option>
              <option value="debit_card">Tarjeta de Débito</option>
              <option value="paypal">PayPal</option>
            </select>
          </div>
        </section>

        {/* Dirección de Envío */}
        <section className="form-section">
          <h3>📍 Dirección de Envío</h3>
          
          <div className="form-group">
            <label>Calle *</label>
            <input
              type="text"
              name="street"
              value={formData.shippingAddress.street}
              onChange={handleAddressChange}
              required
              placeholder="Calle Principal 123"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Ciudad *</label>
              <input
                type="text"
                name="city"
                value={formData.shippingAddress.city}
                onChange={handleAddressChange}
                required
                placeholder="Madrid"
              />
            </div>

            <div className="form-group">
              <label>Estado/Provincia *</label>
              <input
                type="text"
                name="state"
                value={formData.shippingAddress.state}
                onChange={handleAddressChange}
                required
                placeholder="Madrid"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Código Postal *</label>
              <input
                type="text"
                name="zipCode"
                value={formData.shippingAddress.zipCode}
                onChange={handleAddressChange}
                required
                placeholder="28001"
              />
            </div>

            <div className="form-group">
              <label>País *</label>
              <input
                type="text"
                name="country"
                value={formData.shippingAddress.country}
                onChange={handleAddressChange}
                required
              />
            </div>
          </div>
        </section>

        {/* Items */}
        <section className="form-section">
          <h3>📦 Productos</h3>
          
          {formData.items.map((item, index) => (
            <div key={index} className="item-group">
              <div className="item-header">
                <h4>Producto {index + 1}</h4>
                {formData.items.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeItem(index)}
                    className="remove-item-btn"
                  >
                    ✕
                  </button>
                )}
              </div>

              <div className="form-group">
                <label>ID Producto *</label>
                <input
                  type="text"
                  value={item.productId}
                  onChange={(e) => handleItemChange(index, 'productId', e.target.value)}
                  required
                  placeholder="prod-101"
                />
              </div>

              <div className="form-group">
                <label>Nombre *</label>
                <input
                  type="text"
                  value={item.name}
                  onChange={(e) => handleItemChange(index, 'name', e.target.value)}
                  required
                  placeholder="Laptop HP 15"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Cantidad *</label>
                  <input
                    type="number"
                    min="1"
                    value={item.quantity}
                    onChange={(e) => handleItemChange(index, 'quantity', e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Precio *</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={item.price}
                    onChange={(e) => handleItemChange(index, 'price', e.target.value)}
                    required
                  />
                </div>
              </div>
            </div>
          ))}

          <button
            type="button"
            onClick={addItem}
            className="add-item-btn"
          >
            ➕ Agregar Producto
          </button>
        </section>

        {/* Total */}
        <div className="order-total-section">
          <h3>Total: ${calculateTotal()}</h3>
        </div>

        {/* Botones */}
        <div className="form-actions">
          <button type="button" onClick={onCancel} className="cancel-btn">
            Cancelar
          </button>
          <button type="submit" className="submit-btn">
            Crear Orden
          </button>
        </div>
      </form>
    </div>
  );
}

export default OrderForm;
