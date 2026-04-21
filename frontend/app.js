// Pharma Supply Chain Tracking System - Frontend JavaScript

// API Configuration
const API_BASE_URL = 'https://pharma-chain-backend.onrender.com/api';

// Global Variables
let currentUser = {
    address: null,
    role: null,
    connected: false
};

let html5QrCode = null;

// DOM Elements
const elements = {
    // Navigation
    navBtns: document.querySelectorAll('.nav-btn'),
    pages: document.querySelectorAll('.page'),
    
    // User Interface
    roleSelect: document.getElementById('roleSelect'),
    connectWalletBtn: document.getElementById('connectWallet'),
    
    // Verify Page
    startScanBtn: document.getElementById('startScan'),
    batchIdVerify: document.getElementById('batchIdVerify'),
    verifyBtn: document.getElementById('verifyBtn'),
    verificationResult: document.getElementById('verificationResult'),
    
    // Add Drug Page
    addDrugForm: document.getElementById('addDrugForm'),
    addResult: document.getElementById('addResult'),
    
    // Transfer Page
    transferForm: document.getElementById('transferForm'),
    transferResult: document.getElementById('transferResult'),
    
    // Inventory Page
    searchInventory: document.getElementById('searchInventory'),
    refreshInventory: document.getElementById('refreshInventory'),
    importFromHF: document.getElementById('importFromHF'),
    importResult: document.getElementById('importResult'),
    inventoryBody: document.getElementById('inventoryBody'),
    
    // Utilities
    loadingOverlay: document.getElementById('loadingOverlay'),
    toast: document.getElementById('toast'),
    toastMessage: document.getElementById('toastMessage'),
    toastClose: document.querySelector('.toast-close')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    setupEventListeners();
    loadInventory();
    checkWalletConnection();
}

// Event Listeners Setup
function setupEventListeners() {
    // Navigation
    elements.navBtns.forEach(btn => {
        btn.addEventListener('click', () => switchPage(btn.dataset.page));
    });
    
    // Role Selection
    elements.roleSelect.addEventListener('change', handleRoleChange);
    
    // Wallet Connection
    elements.connectWalletBtn.addEventListener('click', connectWallet);
    
    // Verify Page
    elements.startScanBtn.addEventListener('click', startQRScanner);
    elements.verifyBtn.addEventListener('click', verifyDrug);
    elements.batchIdVerify.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') verifyDrug();
    });
    
    // Add Drug Page
    elements.addDrugForm.addEventListener('submit', addDrug);
    
    // Transfer Page
    elements.transferForm.addEventListener('submit', transferDrug);
    
    // Inventory Page
    elements.refreshInventory.addEventListener('click', loadInventory);
    elements.searchInventory.addEventListener('input', filterInventory);
    elements.importFromHF.addEventListener('click', importFromHuggingFace);
    
    // Toast Close Button
    if (elements.toastClose) {
        elements.toastClose.addEventListener('click', () => {
            elements.toast.classList.add('hidden');
        });
    }
}

// Page Navigation
function switchPage(pageName) {
    // Update navigation buttons
    elements.navBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.page === pageName);
    });
    
    // Update pages
    elements.pages.forEach(page => {
        page.classList.toggle('active', page.id === `${pageName}-page`);
    });
    
    // Load page-specific data
    if (pageName === 'inventory') {
        loadInventory();
    }
}

// Role Management
function handleRoleChange() {
    const role = elements.roleSelect.value;
    currentUser.role = role;
    
    // Show/hide features based on role
    updateUIForRole(role);
    
    if (role) {
        showToast(`Role set to: ${role.charAt(0).toUpperCase() + role.slice(1)}`, 'success');
    }
}

function updateUIForRole(role) {
    const addDrugBtn = document.querySelector('[data-page="add"]');
    const transferBtn = document.querySelector('[data-page="transfer"]');
    
    // Only manufacturers can add drugs
    if (addDrugBtn) {
        addDrugBtn.style.display = role === 'manufacturer' ? 'flex' : 'none';
    }
    
    // Distributors and pharmacies can transfer drugs
    if (transferBtn) {
        const canTransfer = role === 'distributor' || role === 'pharmacy';
        transferBtn.style.display = canTransfer ? 'flex' : 'none';
    }
}

// Wallet Connection
async function connectWallet() {
    try {
        showLoading(true);
        
        if (typeof window.ethereum !== 'undefined') {
            // Request account access
            const accounts = await window.ethereum.request({
                method: 'eth_requestAccounts'
            });
            
            if (accounts.length > 0) {
                currentUser.address = accounts[0];
                currentUser.connected = true;
                
                elements.connectWalletBtn.innerHTML = `
                    <i class="fas fa-check"></i> 
                    ${currentUser.address.substring(0, 6)}...${currentUser.address.substring(38)}
                `;
                elements.connectWalletBtn.classList.add('connected');
                
                showToast('Wallet connected successfully!', 'success');
                
                // Assign role to user (for demo purposes)
                if (currentUser.role) {
                    await assignUserRole(currentUser.address, currentUser.role);
                }
            }
        } else {
            showToast('MetaMask is not installed. Please install MetaMask to continue.', 'error');
        }
    } catch (error) {
        console.error('Wallet connection error:', error);
        showToast('Failed to connect wallet', 'error');
    } finally {
        showLoading(false);
    }
}

function checkWalletConnection() {
    if (typeof window.ethereum !== 'undefined') {
        window.ethereum.request({ method: 'eth_accounts' })
            .then(accounts => {
                if (accounts.length > 0) {
                    currentUser.address = accounts[0];
                    currentUser.connected = true;
                    elements.connectWalletBtn.innerHTML = `
                        <i class="fas fa-check"></i> 
                        ${currentUser.address.substring(0, 6)}...${currentUser.address.substring(38)}
                    `;
                    elements.connectWalletBtn.classList.add('connected');
                }
            })
            .catch(error => {
                console.error('Error checking wallet connection:', error);
            });
    }
}

// QR Scanner
function startQRScanner() {
    if (html5QrCode) {
        html5QrCode.stop().then(() => {
            html5QrCode = null;
            elements.startScanBtn.innerHTML = '<i class="fas fa-camera"></i> Start QR Scanner';
        });
        return;
    }
    
    html5QrCode = new Html5Qrcode("qr-reader");
    
    Html5Qrcode.getCameras().then(devices => {
        if (devices && devices.length) {
            const cameraId = devices[0].id;
            
            html5QrCode.start(
                cameraId,
                {
                    fps: 10,
                    qrbox: { width: 250, height: 250 }
                },
                (decodedText, decodedResult) => {
                    // Handle successful scan
                    handleQRCodeScan(decodedText);
                },
                (errorMessage) => {
                    // Handle scan error silently
                }
            ).then(() => {
                elements.startScanBtn.innerHTML = '<i class="fas fa-stop"></i> Stop Scanner';
            }).catch((err) => {
                console.error(`Unable to start scanning: ${err}`);
                showToast('Failed to start camera. Please use manual input instead.', 'error');
                html5QrCode = null;
                elements.startScanBtn.innerHTML = '<i class="fas fa-camera"></i> Start QR Scanner';
            });
        } else {
            showToast('No camera found. Please use manual batch ID input.', 'warning');
        }
    }).catch(err => {
        console.error(`Error getting cameras: ${err}`);
        showToast('Camera access not available. Please use manual batch ID input.', 'warning');
        html5QrCode = null;
    });
}

function handleQRCodeScan(decodedText) {
    // Stop scanner
    if (html5QrCode) {
        html5QrCode.stop().then(() => {
            html5QrCode = null;
            elements.startScanBtn.innerHTML = '<i class="fas fa-camera"></i> Start QR Scanner';
        });
    }
    
    // Extract batch ID from QR code
    const batchId = decodedText.replace('DRUG:', '');
    elements.batchIdVerify.value = batchId;
    
    // Auto-verify
    verifyDrug();
}

// API Functions
async function verifyDrug() {
    const batchId = elements.batchIdVerify.value.trim();
    
    if (!batchId) {
        showToast('Please enter a batch ID', 'error');
        return;
    }
    
    try {
        showLoading(true);
        
        const response = await fetch(`${API_BASE_URL}/drugs/verify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ batch_id: batchId })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayVerificationResult(data);
        } else {
            showToast(data.detail || 'Verification failed', 'error');
        }
    } catch (error) {
        console.error('Verification error:', error);
        showToast('Network error. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

async function addDrug(event) {
    event.preventDefault();
    
    if (currentUser.role !== 'manufacturer') {
        showToast('Only manufacturers can add drugs', 'error');
        return;
    }
    
    const formData = new FormData(elements.addDrugForm);
    const drugData = {
        batch_id: formData.get('batchId'),
        name: formData.get('drugName'),
        manufacturer: formData.get('manufacturer'),
        manufacture_date: formData.get('manufactureDate'),
        expiry_date: formData.get('expiryDate')
    };
    
    try {
        showLoading(true);
        
        const response = await fetch(`${API_BASE_URL}/drugs`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(drugData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showResult(elements.addResult, 'Drug added successfully!', 'success');
            elements.addDrugForm.reset();
            
            // Show QR code
            if (data.qr_code) {
                const qrHtml = `
                    <div class="qr-code">
                        <h4>Generated QR Code:</h4>
                        <img src="${data.qr_code}" alt="QR Code for ${drugData.batch_id}">
                        <p>Batch ID: ${drugData.batch_id}</p>
                    </div>
                `;
                elements.addResult.innerHTML += qrHtml;
            }
            
            // Refresh inventory
            loadInventory();
        } else {
            showResult(elements.addResult, data.detail || 'Failed to add drug', 'error');
        }
    } catch (error) {
        console.error('Add drug error:', error);
        showResult(elements.addResult, 'Network error. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

async function transferDrug(event) {
    event.preventDefault();
    
    if (!currentUser.connected) {
        showToast('Please connect your wallet first', 'error');
        return;
    }
    
    const formData = new FormData(elements.transferForm);
    const transferData = {
        batch_id: formData.get('transferBatchId'),
        new_owner_address: formData.get('newOwnerAddress'),
        new_owner_name: formData.get('newOwnerName')
    };
    
    try {
        showLoading(true);
        
        const response = await fetch(`${API_BASE_URL}/drugs/transfer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(transferData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showResult(elements.transferResult, 'Drug transferred successfully!', 'success');
            elements.transferForm.reset();
            loadInventory();
        } else {
            showResult(elements.transferResult, data.detail || 'Transfer failed', 'error');
        }
    } catch (error) {
        console.error('Transfer drug error:', error);
        showResult(elements.transferResult, 'Network error. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

async function loadInventory() {
    try {
        const response = await fetch(`${API_BASE_URL}/drugs`);
        const data = await response.json();
        
        if (response.ok) {
            displayInventory(data.drugs);
        } else {
            showToast('Failed to load inventory', 'error');
        }
    } catch (error) {
        console.error('Load inventory error:', error);
        showToast('Network error. Please try again.', 'error');
    }
}

async function importFromHuggingFace() {
    try {
        showLoading(true);
        
        const response = await fetch(`${API_BASE_URL}/drugs/import-huggingface`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                dataset_name: 'Fda/Drug-Labeling',
                max_records: 50
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showResult(elements.importResult, `Successfully imported ${data.imported_count} drugs from Hugging Face!`, 'success');
            showToast(`Imported ${data.imported_count} drugs`, 'success');
            
            // Refresh inventory to show imported drugs
            loadInventory();
        } else {
            showResult(elements.importResult, data.message || 'Failed to import drugs', 'error');
            showToast('Import failed', 'error');
        }
    } catch (error) {
        console.error('Import from Hugging Face error:', error);
        showResult(elements.importResult, 'Network error. Please try again.', 'error');
        showToast('Network error during import', 'error');
    } finally {
        showLoading(false);
    }
}

async function assignUserRole(address, role) {
    try {
        const response = await fetch(`${API_BASE_URL}/users/role`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                address: address,
                role: role,
                name: `User ${address.substring(0, 6)}`
            })
        });
        
        if (!response.ok) {
            console.error('Failed to assign role');
        }
    } catch (error) {
        console.error('Assign role error:', error);
    }
}

// Display Functions
function displayVerificationResult(data) {
    const resultClass = data.is_genuine ? 'success' : 'error';
    const statusIcon = data.is_genuine ? 'fa-check-circle' : 'fa-times-circle';
    const statusText = data.is_genuine ? 'GENUINE' : 'COUNTERFEIT';
    
    let html = `
        <div class="drug-card">
            <div class="drug-card-header">
                <h3><i class="fas ${statusIcon}"></i> Verification Result: ${statusText}</h3>
            </div>
            <div class="drug-card-body">
                <div class="drug-info">
                    <div class="drug-info-item">
                        <span class="drug-info-label">Batch ID:</span>
                        <span class="drug-info-value">${data.batch_id || 'N/A'}</span>
                    </div>
                    <div class="drug-info-item">
                        <span class="drug-info-label">Drug Name:</span>
                        <span class="drug-info-value">${data.drug_name || 'N/A'}</span>
                    </div>
                    <div class="drug-info-item">
                        <span class="drug-info-label">Current Owner:</span>
                        <span class="drug-info-value">${data.current_owner || 'N/A'}</span>
                    </div>
                    <div class="drug-info-item">
                        <span class="drug-info-label">Status:</span>
                        <span class="drug-info-value">
                            <span class="status-badge ${data.is_active ? 'status-active' : 'status-recalled'}">
                                ${data.is_active ? 'Active' : 'Recalled'}
                            </span>
                        </span>
                    </div>
                    <div class="drug-info-item">
                        <span class="drug-info-label">Expiry Status:</span>
                        <span class="drug-info-value">
                            <span class="status-badge ${data.is_expired ? 'status-expired' : 'status-active'}">
                                ${data.is_expired ? 'Expired' : 'Valid'}
                            </span>
                        </span>
                    </div>
                </div>
    `;
    
    // Add drug interaction warnings if present
    if (data.interactions && data.interactions.length > 0) {
        html += `
            <div class="interaction-warnings">
                <h4><i class="fas fa-exclamation-triangle"></i> Drug Interaction Warnings</h4>
                <div class="interaction-list">
        `;
        data.interactions.forEach(interaction => {
            const severityClass = interaction.severity === 'high' ? 'interaction-high' : 'interaction-moderate';
            html += `
                <div class="interaction-item ${severityClass}">
                    <strong>${interaction.drug}</strong>
                    <span class="interaction-severity">${interaction.severity} severity</span>
                    <small>Confidence: ${(interaction.confidence * 100).toFixed(1)}%</small>
                </div>
            `;
        });
        html += `
                </div>
            </div>
        `;
    }
    
    if (data.ownership_history && data.ownership_history.length > 0) {
        html += `
            <div class="ownership-history">
                <h4><i class="fas fa-history"></i> Supply Chain History</h4>
                <div class="timeline">
        `;
        
        data.ownership_history.forEach((owner, index) => {
            html += `
                <div class="timeline-item">
                    <strong>${owner}</strong>
                    <small>Step ${index + 1}</small>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    }
    
    if (data.qr_code) {
        html += `
            <div class="qr-code">
                <h4><i class="fas fa-qrcode"></i> Drug QR Code</h4>
                <img src="${data.qr_code}" alt="QR Code">
            </div>
        `;
    }
    
    html += `
            </div>
        </div>
    `;
    
    elements.verificationResult.innerHTML = html;
    elements.verificationResult.classList.remove('hidden');
}

function displayInventory(drugs) {
    if (!drugs || drugs.length === 0) {
        elements.inventoryBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">No drugs found in inventory</td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    drugs.forEach(drug => {
        const expiryDate = new Date(drug.expiry_date);
        const isExpired = expiryDate < new Date();
        const statusClass = isExpired ? 'status-expired' : 'status-active';
        const statusText = isExpired ? 'Expired' : 'Active';
        
        html += `
            <tr>
                <td><strong>${drug.batch_id}</strong></td>
                <td>${drug.name}</td>
                <td>${drug.manufacturer}</td>
                <td>${formatDate(drug.manufacture_date)}</td>
                <td>${formatDate(drug.expiry_date)}</td>
                <td>
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="viewDrugDetails('${drug.batch_id}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                </td>
            </tr>
        `;
    });
    
    elements.inventoryBody.innerHTML = html;
}

function viewDrugDetails(batchId) {
    elements.batchIdVerify.value = batchId;
    switchPage('verify');
    verifyDrug();
}

function filterInventory() {
    const searchTerm = elements.searchInventory.value.toLowerCase();
    const rows = elements.inventoryBody.getElementsByTagName('tr');
    
    Array.from(rows).forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
}

// Utility Functions
function showLoading(show) {
    elements.loadingOverlay.classList.toggle('hidden', !show);
}

function showToast(message, type = 'success') {
    elements.toastMessage.textContent = message;
    elements.toast.className = `toast ${type}`;
    elements.toast.classList.remove('hidden');
    
    setTimeout(() => {
        elements.toast.classList.add('hidden');
    }, 3000);
}

function showResult(element, message, type) {
    element.textContent = message;
    element.className = `result-message ${type} show`;
    
    setTimeout(() => {
        element.classList.remove('show');
    }, 5000);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Form Validation
function validateEthereumAddress(address) {
    return /^0x[a-fA-F0-9]{40}$/.test(address);
}

function validateBatchId(batchId) {
    return /^[A-Z0-9-]+$/.test(batchId);
}

// Add custom validation
document.getElementById('newOwnerAddress').addEventListener('input', function(e) {
    const address = e.target.value;
    if (address && !validateEthereumAddress(address)) {
        e.target.setCustomValidity('Please enter a valid Ethereum address (0x...)');
    } else {
        e.target.setCustomValidity('');
    }
});

document.getElementById('batchId').addEventListener('input', function(e) {
    const batchId = e.target.value;
    if (batchId && !validateBatchId(batchId)) {
        e.target.setCustomValidity('Batch ID should contain only uppercase letters, numbers, and hyphens');
    } else {
        e.target.setCustomValidity('');
    }
});

// Set default dates
document.addEventListener('DOMContentLoaded', function() {
    const now = new Date();
    const manufactureDate = now.toISOString().slice(0, 16);
    const expiryDate = new Date(now.setFullYear(now.getFullYear() + 2)).toISOString().slice(0, 16);
    
    const manufactureInput = document.getElementById('manufactureDate');
    const expiryInput = document.getElementById('expiryDate');
    
    if (manufactureInput) manufactureInput.value = manufactureDate;
    if (expiryInput) expiryInput.value = expiryDate;
});
