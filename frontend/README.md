# Xray Panel - Frontend

React + TypeScript + Mantine UI frontend for the Xray Control Panel.

## Features

- Modern UI with Mantine components
- Dark/Light theme support
- Real-time updates
- Responsive design
- Type-safe API client

## Development

Install dependencies:
```bash
npm install
```

Start dev server:
```bash
npm run dev
```

Build for production:
```bash
npm run build
```

## Environment Variables

Create `.env` file:
```
VITE_API_URL=http://localhost:8000
```

## Project Structure

```
src/
├── components/     # Reusable components
├── pages/          # Page components
├── services/       # API client
├── stores/         # Zustand stores
├── types/          # TypeScript types
├── hooks/          # Custom hooks
└── utils/          # Utilities
```
