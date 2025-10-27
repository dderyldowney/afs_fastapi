# AFS FastAPI Farm UI

**Agricultural Robotics Management Interface for Multi-Tractor Coordination**

This React application provides a web-based management interface for the AFS FastAPI agricultural robotics platform, enabling real-time monitoring and control of multi-tractor field operations.

## 🚜 Agricultural Features

- **Tractor Tracking**: Real-time location and status monitoring for agricultural equipment
- **Field Management**: Field boundary definition, crop planning, and operation scheduling
- **API Integration**: Direct communication with AFS FastAPI backend for equipment control
- **Design System**: Consistent agricultural-themed UI components

## 🛠 Development Setup

### Prerequisites

```bash
# Ensure AFS FastAPI backend is running
cd ../../
python -m afs_fastapi
# Backend available at http://localhost:8000
```

### Installation & Development

```bash
# Install dependencies
npm install

# Start development server
npm start
# Opens http://localhost:3000 automatically
```

### Available Scripts

| Command | Description |
|---------|-------------|
| `npm start` | Development server with hot reload |
| `npm test` | Run test suite in interactive watch mode |
| `npm run build` | Production build for deployment |
| `npm run eject` | Eject from Create React App (irreversible) |

## 🌾 Agricultural Architecture

### Core Components

```
src/
├── features/
│   ├── tractor_tracking/      # Real-time equipment monitoring
│   └── field_management/      # Agricultural field operations
├── api/                       # AFS FastAPI integration
└── design_system/            # Agricultural UI components
```

### Backend Integration

The farm UI connects to the AFS FastAPI backend for:

- **Equipment Control**: FarmTractor class with 40+ attributes
- **Fleet Coordination**: Multi-tractor synchronization via Vector Clock
- **Field Operations**: ISOBUS-compliant agricultural protocols
- **Safety Systems**: ISO 18497 safety compliance monitoring

## 📚 Documentation

- **API Integration**: [src/api_integration.md](src/api_integration.md)
- **Design System**: [src/design_system.md](src/design_system.md)
- **Tractor Tracking**: [src/features/tractor_tracking.md](src/features/tractor_tracking.md)
- **Field Management**: [src/features/field_management.md](src/features/field_management.md)

## 🔗 Related Projects

- **Backend**: [../../README.md](../../README.md) - AFS FastAPI agricultural robotics platform
- **Documentation**: [../../docs/README.md](../../docs/README.md) - Complete documentation tree

## 🚀 Deployment

```bash
# Production build
npm run build

# Deploy to static hosting
# Build output: ./build/
```

The built application can be deployed to any static hosting service and configured to connect to your AFS FastAPI backend deployment.

---

**Part of the AFS FastAPI Agricultural Robotics Platform**
For complete agricultural equipment integration and multi-tractor coordination capabilities.
