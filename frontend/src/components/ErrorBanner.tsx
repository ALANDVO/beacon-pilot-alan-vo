/** Error Banner Component */
import { X, AlertCircle } from 'lucide-react';
import './ErrorBanner.css';

interface ErrorBannerProps {
  message: string | null;
  onDismiss: () => void;
}

export function ErrorBanner({ message, onDismiss }: ErrorBannerProps) {
  if (!message) return null;

  return (
    <div className="error-banner" role="alert">
      <AlertCircle className="icon" size={20} />
      <span className="message">{message}</span>
      <button className="dismiss-btn" onClick={onDismiss} aria-label="Dismiss error">
        <X className="icon" size={18} />
      </button>
    </div>
  );
}