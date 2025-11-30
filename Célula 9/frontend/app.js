// Configuración - Reemplazar con valores reales después del despliegue
const CONFIG = {
    apiEndpoint: 'https://YOUR_API_GATEWAY_URL',
    userPoolId: 'YOUR_USER_POOL_ID',
    clientId: 'YOUR_CLIENT_ID',
    region: 'us-east-1'
};

let authToken = null;

// Funciones de Autenticación
function showLoginForm() {
    document.getElementById('login-modal').style.display = 'flex';
}

function hideLoginForm() {
    document.getElementById('login-modal').style.display = 'none';
}

async function login() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    try {
        // Aquí iría la integración real con Cognito
        // Por ahora simulamos el login
        authToken = 'simulated-token-' + Date.now();
        
        document.getElementById('login-btn').style.display = 'none';
        document.getElementById('logout-btn').style.display = 'inline-block';
        document.getElementById('user-info').textContent = `Usuario: ${email}`;
        document.getElementById('main-content').style.display = 'block';
        hideLoginForm();
        
        loadGadgets();
    } catch (error) {
        alert('Error al iniciar sesión: ' + error.message);
    }
}

function logout() {
    authToken = null;
    document.getElementById('login-btn').style.display = 'inline-block';
    document.getElementById('logout-btn').style.display = 'none';
    document.getElementById('user-info').textContent = '';
    document.getElementById('main-content').style.display = 'none';
}

// Funciones CRUD
function showCreateForm() {
    document.getElementById('create-form').style.display = 'block';
}

function hideCreateForm() {
    document.getElementById('create-form').style.display = 'none';
    document.getElementById('gadget-form').reset();
}

document.getElementById('gadget-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    await createGadget();
});

async function createGadget() {
    const gadget = {
        Name: document.getElementById('name').value,
        Category: document.getElementById('category').value,
        MaxSpeed: document.getElementById('maxSpeed').value,
        PropulsionType: document.getElementById('propulsionType').value,
        Seats: parseInt(document.getElementById('seats').value),
        Status: document.getElementById('status').value
    };

    try {
        const response = await fetch(`${CONFIG.apiEndpoint}/gadgets`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(gadget)
        });

        if (response.ok) {
            alert('Gadget creado exitosamente');
            hideCreateForm();
            loadGadgets();
        } else {
            alert('Error al crear gadget');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function loadGadgets() {
    try {
        const response = await fetch(`${CONFIG.apiEndpoint}/gadgets`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const gadgets = await response.json();
            displayGadgets(gadgets);
        } else {
            alert('Error al cargar gadgets');
        }
    } catch (error) {
        console.error('Error:', error);
        // Cargar datos de ejemplo si falla
        loadSampleData();
    }
}

function displayGadgets(gadgets) {
    const container = document.getElementById('gadgets-container');
    container.innerHTML = '';

    gadgets.forEach(gadget => {
        const card = document.createElement('div');
        card.className = 'gadget-card';
        card.innerHTML = `
            <h3>${gadget.Name}</h3>
            <p><strong>Categoría:</strong> ${gadget.Category}</p>
            <p><strong>Velocidad Máxima:</strong> ${gadget.MaxSpeed}</p>
            <p><strong>Propulsión:</strong> ${gadget.PropulsionType}</p>
            <p><strong>Asientos:</strong> ${gadget.Seats}</p>
            <p><strong>Estado:</strong> <span class="status-${gadget.Status.toLowerCase()}">${gadget.Status}</span></p>
            <p><strong>Creado:</strong> ${new Date(gadget.CreatedAt).toLocaleDateString()}</p>
            <div class="actions">
                <button onclick="editGadget('${gadget.GadgetId}')">✏️ Editar</button>
                <button onclick="deleteGadget('${gadget.GadgetId}')">🗑️ Eliminar</button>
            </div>
        `;
        container.appendChild(card);
    });
}

async function editGadget(id) {
    const newName = prompt('Nuevo nombre:');
    if (!newName) return;

    try {
        const response = await fetch(`${CONFIG.apiEndpoint}/gadgets/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ Name: newName })
        });

        if (response.ok) {
            alert('Gadget actualizado');
            loadGadgets();
        } else {
            alert('Error al actualizar');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function deleteGadget(id) {
    if (!confirm('¿Estás seguro de eliminar este gadget?')) return;

    try {
        const response = await fetch(`${CONFIG.apiEndpoint}/gadgets/${id}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok || response.status === 204) {
            alert('Gadget eliminado');
            loadGadgets();
        } else {
            alert('Error al eliminar');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Cargar datos de ejemplo para demostración
async function loadSampleData() {
    try {
        const response = await fetch('../data/vehicle_gadgets_sample.json');
        const gadgets = await response.json();
        displayGadgets(gadgets);
    } catch (error) {
        console.error('Error cargando datos de ejemplo:', error);
    }
}
