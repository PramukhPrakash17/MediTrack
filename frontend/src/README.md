# MediTrack Frontend Structure

This document describes the organized structure of the MediTrack frontend application.

## Project Structure

```
src/
├── api/                    # API client and authentication utilities
│   ├── client.js          # Base API client
│   └── withAuthClient.js  # Authenticated API client wrapper
├── auth/                   # Authentication context and utilities
│   └── AuthContext.js     # React context for authentication state
├── components/             # Reusable UI components
│   ├── Features/          # Features component
│   │   ├── index.js       # Component logic
│   │   └── styles.css     # Component styles
│   ├── Hero/              # Hero section component
│   │   ├── index.js       # Component logic
│   │   └── styles.css     # Component styles
│   └── Navbar/            # Navigation component
│       ├── index.js       # Component logic
│       └── styles.css     # Component styles
├── pages/                  # Page components
│   ├── AuthPage/          # Authentication page
│   │   └── index.js       # Page logic (inline styles)
│   └── ServicesPage/      # Services/Patient records page
│       ├── index.js       # Page logic
│       └── styles.css     # Page styles
├── App.js                 # Main application component
├── App.css               # Global application styles
├── index.js              # Application entry point
└── index.css             # Global styles
```

## Component Organization

### Pages

Each page is organized in its own folder with:

- `index.js` - Main component logic
- `styles.css` - Page-specific styles (if needed)

### Components

Each reusable component is organized in its own folder with:

- `index.js` - Component logic
- `styles.css` - Component-specific styles

## Benefits of This Structure

1. **Modularity**: Each component/page is self-contained
2. **Maintainability**: Easy to find and modify specific components
3. **Scalability**: Easy to add new components/pages
4. **Clarity**: Clear separation of concerns
5. **Reusability**: Components can be easily reused across pages

## Import Patterns

### Importing Components

```javascript
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import Features from "./components/Features";
```

### Importing Pages

```javascript
import AuthPage from "./pages/AuthPage";
import ServicesPage from "./pages/ServicesPage";
```

### Importing Styles

```javascript
import "./styles.css"; // Within component folders
```

## Adding New Components/Pages

1. Create a new folder in `components/` or `pages/`
2. Add `index.js` for the component logic
3. Add `styles.css` for styling (if needed)
4. Update imports in other files as needed
