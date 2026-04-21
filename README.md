# Pharma Supply Chain Tracking System

A blockchain-based pharmaceutical drug tracking system that ensures transparency and prevents counterfeit drugs in the supply chain using Ethereum smart contracts and FastAPI.

## 🌟 Features

- **Blockchain Integration**: Ethereum smart contracts for immutable drug tracking
- **Supply Chain Transparency**: Complete ownership history from manufacturer to pharmacy
- **QR Code Generation**: Unique QR codes for each drug batch
- **Role-Based Access**: Manufacturer, Distributor, and Pharmacy roles
- **Real-time Verification**: Instant drug authenticity verification
- **MetaMask Integration**: Connect with Ethereum wallet
- **Responsive Web Interface**: Modern, mobile-friendly UI

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Blockchain    │
│   (HTML/JS)     │◄──►│   (FastAPI)     │◄──►│   (Ethereum)    │
│                 │    │                 │    │                 │
│ - User Interface│    │ - REST API      │    │ - Smart Contract│
│ - QR Scanner    │    │ - Web3.py       │    │ - Drug Records  │
│ - MetaMask      │    │ - SQLite        │    │ - Ownership     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Project Structure

```
pharma-supply-chain/
├── backend/
│   ├── app.py                 # FastAPI application
│   └── .env.example          # Environment variables template
├── frontend/
│   ├── index.html            # Main frontend application
│   ├── styles.css            # Styling
│   └── app.js                # Frontend JavaScript
├── contracts/
│   └── PharmaSupplyChain.sol # Solidity smart contract
├── scripts/
│   └── deploy_contract.py    # Contract deployment script
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 14+
- MetaMask browser extension
- Ethereum account with Sepolia testnet ETH

### 1. Clone and Setup

```bash
git clone <repository-url>
cd pharma-supply-chain
```

### 2. Install Dependencies

**Backend Dependencies:**
```bash
pip install -r requirements.txt
```

**Additional Python packages:**
```bash
pip install py-solc-x
```

### 3. Configure Environment

Copy the environment template and configure:
```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your configuration:
```env
INFURA_PROJECT_ID=your-infura-project-id
CONTRACT_ADDRESS=0x0000000000000000000000000000000000000000
PRIVATE_KEY=your-private-key-here
```

### 4. Deploy Smart Contract

```bash
cd scripts
python deploy_contract.py
```

This will:
- Compile the Solidity contract
- Deploy to Sepolia testnet
- Update backend configuration
- Save deployment information

### 5. Start Backend Server

```bash
cd backend
python app.py
```

The API will be available at `http://localhost:8000`

### 6. Open Frontend

Open `frontend/index.html` in your browser or serve it with a web server:

```bash
# Using Python's built-in server
cd frontend
python -m http.server 3000
```

Then visit `http://localhost:3000`

## 🔧 Detailed Setup

### Getting Sepolia Testnet ETH

1. Install MetaMask browser extension
2. Switch to Sepolia testnet
3. Get test ETH from a faucet:
   - [Sepolia Faucet](https://sepoliafaucet.com/)
   - [Alchemy Sepolia Faucet](https://sepoliafaucet.com/)

### Getting Infura Project ID

1. Sign up at [Infura](https://infura.io/)
2. Create a new project
3. Copy the Project ID
4. Add it to your `.env` file

### Smart Contract Functions

| Function | Description | Access |
|----------|-------------|---------|
| `addDrug()` | Add new drug batch | Manufacturer |
| `transferDrug()` | Transfer ownership | Current Owner |
| `getDrug()` | Get drug details | Public |
| `verifyDrug()` | Verify authenticity | Public |
| `assignRole()` | Assign user role | Admin |

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/drugs` | POST | Add new drug |
| `/api/drugs/transfer` | POST | Transfer drug |
| `/api/drugs/verify` | POST | Verify drug |
| `/api/drugs/{batch_id}` | GET | Get drug details |
| `/api/drugs` | GET | List all drugs |
| `/api/users/role` | POST | Assign user role |
| `/api/health` | GET | Health check |

## 🎯 Usage Guide

### 1. Setup User Role

1. Open the web application
2. Select your role (Manufacturer/Distributor/Pharmacy)
3. Connect your MetaMask wallet

### 2. For Manufacturers

1. Navigate to "Add Drug" page
2. Fill in drug details:
   - Batch ID (unique identifier)
   - Drug name
   - Manufacturer name
   - Manufacture date
   - Expiry date
3. Click "Add Drug Batch"
4. Save the generated QR code

### 3. For Distributors

1. Navigate to "Transfer Drug" page
2. Enter batch ID received from manufacturer
3. Add pharmacy address and name
4. Click "Transfer Drug"

### 4. For Pharmacies

1. Navigate to "Verify Drug" page
2. Scan QR code or enter batch ID
3. View drug authenticity and supply chain history
4. Verify drug is genuine and not expired

### 5. QR Code Scanning

- Click "Start QR Scanner" on verification page
- Allow camera access
- Scan the drug QR code
- View verification results automatically

## 🔒 Security Features

- **Immutable Records**: All transactions stored on blockchain
- **Role-Based Access**: Only authorized users can perform actions
- **Smart Contract Validation**: Business logic enforced at contract level
- **MetaMask Authentication**: Secure wallet-based authentication
- **Input Validation**: Comprehensive validation on frontend and backend

## 🧪 Testing

### Test the System

1. **Add Test Drug**:
   ```json
   {
     "batch_id": "TEST-001",
     "name": "Paracetamol 500mg",
     "manufacturer": "Test Pharma Corp",
     "manufacture_date": "2024-01-01T00:00:00Z",
     "expiry_date": "2026-01-01T00:00:00Z"
   }
   ```

2. **Verify Drug**:
   - Use batch ID "TEST-001"
   - Check authenticity and history

3. **Transfer Drug**:
   - Transfer from manufacturer to distributor
   - Transfer from distributor to pharmacy

## 🐛 Troubleshooting

### Common Issues

**1. Contract Deployment Fails**
- Check Sepolia ETH balance
- Verify Infura Project ID
- Ensure private key is correct

**2. MetaMask Connection Issues**
- Ensure MetaMask is installed
- Check if you're on Sepolia testnet
- Refresh the page and try again

**3. QR Scanner Not Working**
- Allow camera permissions
- Use HTTPS (localhost may not work)
- Try a different browser

**4. Backend Connection Errors**
- Check if backend server is running
- Verify API endpoint URLs
- Check CORS settings

### Debug Mode

Enable debug logging:
```bash
export DEBUG=1
python backend/app.py
```

## 📊 System Flow

1. **Manufacturing**: Manufacturer adds drug batch → Smart contract stores data → QR code generated
2. **Distribution**: Manufacturer transfers to distributor → Ownership updated on blockchain
3. **Retail**: Distributor transfers to pharmacy → Final ownership recorded
4. **Verification**: Customer scans QR code → System verifies authenticity → Shows complete history

## 🔄 Supply Chain Process

```
Manufacturer ──► Distributor ──► Pharmacy ──► Customer
     │              │              │
     ▼              ▼              ▼
  Add Drug     Transfer Drug   Verify Drug
     │              │              │
     └─────── Blockchain Storage ────────┘
```

## 🛡️ Anti-Counterfeit Measures

- **Unique Batch IDs**: Each drug batch has a unique identifier
- **Blockchain Immutability**: Records cannot be altered once created
- **Complete Traceability**: Full ownership history visible
- **Real-time Verification**: Instant authenticity checks
- **Expiry Tracking**: Automatic expiry status updates

## 🚀 Future Enhancements

- [ ] Mobile app development
- [ ] Integration with ERP systems
- [ ] Advanced analytics dashboard
- [ ] Multi-chain support
- [ ] IoT sensor integration
- [ ] Regulatory compliance features
- [ ] Advanced reporting system

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

---

**Built with ❤️ to ensure pharmaceutical safety and transparency**
