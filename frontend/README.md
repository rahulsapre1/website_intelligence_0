# Website Intelligence Frontend

A modern React/Next.js frontend for the Website Intelligence System that provides AI-powered business insights from any website.

## Features

- **Modern UI**: Built with Next.js, TypeScript, and Tailwind CSS
- **Shadcn/ui Components**: Beautiful, accessible UI components
- **URL Analysis**: Enter any website URL to get instant business insights
- **Chat Interface**: Ask follow-up questions about analyzed websites
- **Analysis History**: View and revisit previous analyses
- **Export & Share**: Export results and share analysis links
- **Responsive Design**: Works perfectly on desktop and mobile
- **Real-time Updates**: Live loading states and error handling

## Quick Start

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm run dev
   ```

3. **Open in Browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

## Backend Integration

The frontend connects to the Website Intelligence API running at `http://localhost:8000`.

### API Endpoints Used:
- `POST /api/v1/analyze-simple` - Analyze websites (simplified version)
- `POST /api/v1/chat` - Chat about analyzed websites

### Authentication:
All requests use Bearer token authentication with the key `dev_secret_key_123`.

## Project Structure

```
frontend/
├── src/
│   ├── app/                 # Next.js app router
│   │   ├── page.tsx        # Main dashboard page
│   │   ├── layout.tsx      # Root layout
│   │   └── globals.css     # Global styles
│   ├── components/
│   │   └── ui/             # Shadcn/ui components
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── input.tsx
│   │       ├── badge.tsx
│   │       └── spinner.tsx
│   └── lib/
│       └── utils.ts        # Utility functions
├── tailwind.config.ts      # Tailwind configuration
├── components.json         # Shadcn/ui configuration
└── package.json           # Dependencies
```

## Key Components

### Main Dashboard (`src/app/page.tsx`)
- URL input form with validation
- Analysis results display with loading states
- Chat interface for follow-up questions
- Analysis history sidebar
- Export and share functionality

### UI Components
- **Button**: Various styles and states
- **Card**: Content containers with headers
- **Input**: Form inputs with validation
- **Badge**: Status indicators
- **Spinner**: Loading animations

## Styling

The app uses:
- **Tailwind CSS** for utility-first styling
- **CSS Variables** for theme colors
- **Responsive Design** with mobile-first approach
- **Modern Gradients** and clean aesthetics

## API Integration

The frontend handles:
- ✅ URL validation
- ✅ Loading states during analysis
- ✅ Error handling with user-friendly messages
- ✅ Real-time chat interface
- ✅ Analysis history management
- ✅ Export functionality (JSON download)
- ✅ Share functionality (clipboard/Web Share API)

## Development

### Available Scripts:
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Tech Stack:
- **Next.js 15** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Shadcn/ui** - Component library
- **Lucide React** - Icons
- **Fetch API** - HTTP requests

## Deployment

The frontend is ready for deployment to Vercel:

1. Connect your GitHub repository to Vercel
2. Set build command: `npm run build`
3. Set output directory: `.next`
4. Deploy!

## Environment Variables

No environment variables are required for the frontend as it uses hardcoded API endpoints for development.

For production, you may want to add:
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_API_TOKEN` - API authentication token

## Browser Support

- Chrome/Edge 88+
- Firefox 85+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- ⚡ Fast loading with Next.js optimization
- 📱 Mobile-first responsive design
- 🎨 Smooth animations and transitions
- 🔄 Real-time updates without page refresh
- 💾 Efficient state management

## Contributing

1. Follow the existing code style
2. Use TypeScript for type safety
3. Add proper error handling
4. Test on multiple screen sizes
5. Ensure accessibility compliance

## License

This project is part of the Website Intelligence System.