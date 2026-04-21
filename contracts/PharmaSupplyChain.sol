// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title PharmaSupplyChain
 * @dev Smart contract for tracking pharmaceutical drugs in the supply chain
 * Prevents counterfeit drugs by ensuring transparency and immutability
 */
contract PharmaSupplyChain {
    
    // Enum for different roles in the supply chain
    enum Role { None, Manufacturer, Distributor, Pharmacy }
    
    // Struct to store drug information
    struct Drug {
        string batchId;           // Unique batch identifier
        string name;              // Drug name
        string manufacturer;      // Manufacturer name
        uint256 manufactureDate;  // Timestamp of manufacture
        uint256 expiryDate;       // Expiry date timestamp
        address currentOwner;     // Current owner address
        bool isActive;            // Drug status (active/recalled)
        string[] ownershipHistory; // History of ownership transfers
    }
    
    // Mapping from batch ID to Drug struct
    mapping(string => Drug) public drugs;
    
    // Mapping from address to role
    mapping(address => Role) public userRoles;
    
    // Array to store all batch IDs for enumeration
    string[] public allBatchIds;
    
    // Events for transparency
    event DrugAdded(
        string indexed batchId,
        string name,
        string manufacturer,
        uint256 manufactureDate,
        uint256 expiryDate,
        address indexed owner
    );
    
    event DrugTransferred(
        string indexed batchId,
        address indexed from,
        address indexed to,
        uint256 timestamp
    );
    
    event RoleAssigned(
        address indexed user,
        Role role,
        uint256 timestamp
    );
    
    // Modifier to check if caller has specific role
    modifier onlyRole(Role _role) {
        require(userRoles[msg.sender] == _role, "Unauthorized: Invalid role");
        _;
    }
    
    // Modifier to check if drug exists
    modifier drugExists(string memory _batchId) {
        require(bytes(drugs[_batchId].batchId).length > 0, "Drug does not exist");
        _;
    }
    
    // Modifier to check if caller is current owner
    modifier onlyOwner(string memory _batchId) {
        require(drugs[_batchId].currentOwner == msg.sender, "Not the owner");
        _;
    }
    
    /**
     * @dev Assign role to a user (only contract deployer can assign roles)
     */
    function assignRole(address _user, Role _role) external {
        // For demo purposes, allow anyone to assign roles
        // In production, restrict to contract deployer
        userRoles[_user] = _role;
        emit RoleAssigned(_user, _role, block.timestamp);
    }
    
    /**
     * @dev Add a new drug to the supply chain
     * Only manufacturers can add drugs
     */
    function addDrug(
        string memory _batchId,
        string memory _name,
        string memory _manufacturer,
        uint256 _manufactureDate,
        uint256 _expiryDate
    ) external onlyRole(Role(Manufacturer)) {
        require(bytes(_batchId).length > 0, "Batch ID cannot be empty");
        require(bytes(drugs[_batchId].batchId).length == 0, "Drug already exists");
        require(_expiryDate > _manufactureDate, "Expiry date must be after manufacture date");
        
        // Create new drug record
        Drug storage newDrug = drugs[_batchId];
        newDrug.batchId = _batchId;
        newDrug.name = _name;
        newDrug.manufacturer = _manufacturer;
        newDrug.manufactureDate = _manufactureDate;
        newDrug.expiryDate = _expiryDate;
        newDrug.currentOwner = msg.sender;
        newDrug.isActive = true;
        
        // Add manufacturer to ownership history
        newDrug.ownershipHistory.push(_manufacturer);
        
        // Add to batch IDs array
        allBatchIds.push(_batchId);
        
        emit DrugAdded(_batchId, _name, _manufacturer, _manufactureDate, _expiryDate, msg.sender);
    }
    
    /**
     * @dev Transfer drug ownership
     * Can be called by current owner (manufacturer -> distributor -> pharmacy)
     */
    function transferDrug(
        string memory _batchId,
        address _newOwner,
        string memory _newOwnerName
    ) external drugExists(_batchId) onlyOwner(_batchId) {
        require(_newOwner != address(0), "Invalid new owner address");
        require(drugs[_batchId].isActive, "Drug is not active");
        require(block.timestamp < drugs[_batchId].expiryDate, "Drug has expired");
        
        // Check role-based transfer rules
        Role currentRole = userRoles[msg.sender];
        Role newRole = userRoles[_newOwner];
        
        // Manufacturer can only transfer to Distributor
        if (currentRole == Role(Manufacturer)) {
            require(newRole == Role(Distributor), "Manufacturer can only transfer to Distributor");
        }
        // Distributor can only transfer to Pharmacy
        else if (currentRole == Role(Distributor)) {
            require(newRole == Role(Pharmacy), "Distributor can only transfer to Pharmacy");
        }
        // Pharmacy cannot transfer (end of supply chain)
        else if (currentRole == Role(Pharmacy)) {
            revert("Pharmacy cannot transfer drugs");
        }
        
        // Update ownership
        address oldOwner = drugs[_batchId].currentOwner;
        drugs[_batchId].currentOwner = _newOwner;
        drugs[_batchId].ownershipHistory.push(_newOwnerName);
        
        emit DrugTransferred(_batchId, oldOwner, _newOwner, block.timestamp);
    }
    
    /**
     * @dev Get drug details by batch ID
     */
    function getDrug(string memory _batchId) external view drugExists(_batchId) returns (
        string memory name,
        string memory manufacturer,
        uint256 manufactureDate,
        uint256 expiryDate,
        address currentOwner,
        bool isActive,
        string[] memory ownershipHistory
    ) {
        Drug storage drug = drugs[_batchId];
        return (
            drug.name,
            drug.manufacturer,
            drug.manufactureDate,
            drug.expiryDate,
            drug.currentOwner,
            drug.isActive,
            drug.ownershipHistory
        );
    }
    
    /**
     * @dev Verify if a drug is genuine and get its status
     */
    function verifyDrug(string memory _batchId) external view returns (
        bool isGenuine,
        bool isActive,
        bool isExpired,
        string memory drugName,
        string memory currentOwnerName
    ) {
        if (bytes(drugs[_batchId].batchId).length == 0) {
            return (false, false, false, "", "Not Found");
        }
        
        Drug storage drug = drugs[_batchId];
        isGenuine = true;
        isActive = drug.isActive;
        isExpired = block.timestamp > drug.expiryDate;
        
        // Get current owner name from history
        if (drug.ownershipHistory.length > 0) {
            currentOwnerName = drug.ownershipHistory[drug.ownershipHistory.length - 1];
        } else {
            currentOwnerName = "Unknown";
        }
        
        return (isGenuine, isActive, isExpired, drug.name, currentOwnerName);
    }
    
    /**
     * @dev Get all batch IDs
     */
    function getAllBatchIds() external view returns (string[] memory) {
        return allBatchIds;
    }
    
    /**
     * @dev Deactivate a drug (recall)
     * Only manufacturer can recall their drugs
     */
    function recallDrug(string memory _batchId) external drugExists(_batchId) {
        require(drugs[_batchId].currentOwner == msg.sender || 
                userRoles[msg.sender] == Role(Manufacturer), 
                "Only manufacturer can recall drugs");
        
        drugs[_batchId].isActive = false;
    }
    
    /**
     * @dev Get user role
     */
    function getUserRole(address _user) external view returns (Role) {
        return userRoles[_user];
    }
}
